import logging
import json
import warnings

import requests

from pyOutlook.internal.errors import AuthError, MiscError
from pyOutlook.internal.utils import jsonify_recipients

log = logging.getLogger('pyOutlook')


class Message(object):
    """An object representing an email inside of the OutlookAccount.

        Attributes:
            message_id: A string provided by Outlook identifying this specific email
            body: The body content of the email, including HTML formatting
            subject: The subject of the email
            sender_email: The email of the person who sent this email
            sender_name: The name of the person who sent this email, as provided by Outlook
            to_recipients: A comma separated string of emails who were sent this email in the 'To' field

        """

    def __init__(self, account, message_id: str, body: str, subject: str, sender_email: str, sender_name: str,
                 to_recipients: list, **kwargs):
        self.account = account
        self.message_id = message_id
        self.body = body
        self.subject = subject
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.to_recipients = to_recipients
        self.__is_read = kwargs['is_read']

    def __str__(self):
        return self.subject

    def __repr__(self):
        return str(self)

    @classmethod
    def _json_to_messages(cls, account, json_value):
        return [cls._json_to_message(account, message) for message in json_value['value']]

    @classmethod
    def _json_to_message(cls, account, api_json: dict):
        uid = api_json['Id']
        subject = api_json.get('Subject', '')

        sender = api_json.get('Sender', {}).get('EmailAddress', {})
        sender_email = sender.get('Address', '')
        sender_name = sender.get('Name', '')

        body = api_json.get('Body', {}).get('Content', '')

        to_recipients = api_json.get('ToRecipients', [])
        is_read = api_json['IsRead']

        return_message = Message(account, uid, body, subject, sender_email, sender_name, to_recipients, is_read=is_read)
        return return_message

    def _make_api_call(self, http_type: str, endpoint: str, extra_headers: dict=None, data=None):
        """
        Internal method to handle making calls to the Outlook API and logging both the request and response
        Args:
            http_type: (str) 'post' or 'delete'
            endpoint: (str) The endpoint the request will be made to
            headers: A dict of headers to send to the requests module in addition to Authorization and Content-Type
            data: The data to provide to the requests module

        Raises:
            MiscError: For errors that aren't a 401
            AuthError: For 401 errors

        """

        headers = {"Authorization": "Bearer " + self.account.access_token, "Content-Type": "application/json"}

        if extra_headers is not None:
            headers.update(extra_headers)

        log.debug('Making Outlook API request for message (ID: {}) with Headers: {} Data: {}'
                  .format(self.message_id, headers, data))

        if http_type == 'post':
            r = requests.post(endpoint, headers=headers, data=data)
        elif http_type == 'delete':
            r = requests.delete(endpoint, headers=headers)
        elif http_type == 'patch':
            r = requests.patch(endpoint, headers=headers, data=data)
        else:
            raise NotImplemented

        if r.status_code == 401:
            log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
            raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
        elif r.status_code > 299:
            log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
            raise MiscError('Unhandled error received from Outlook. Check logging output.')
        else:
            # If we try  to log r.json() when there is nothing our tests will fail (even though it's successful...)
            log.debug('Response from Outlook Status: {} Body: {}'.format(r.status_code, r.content))

    def forward_message(self, to_recipients, forward_comment=None):
        """Forward Message to recipients with an optional comment.

        Args:
            to_recipients: Comma separated string or list of recipients to send email to.
            forward_comment: String comment to append to forwarded email.

        Examples:
            >>> email = Message()
            >>> email.forward_message('john.doe@domain.com, betsy.donalds@domain.com')
            >>> email.forward_message('john.doe@domain.com', 'Hey Joe')

        Raises:
            MiscError: A comma separated string of emails, or one string email, must be provided
            AuthError: Raised if Outlook returns a 401, generally caused by an invalid or expired access token.

        """
        payload = '{'
        if forward_comment is not None:
            payload += '"Comment" : "' + str(forward_comment) + '",'
        if to_recipients is None:
            raise MiscError('To Recipients is not defined. Can not forward message.')

        payload += '"ToRecipients" : [' + jsonify_recipients(to_recipients, 'to', True) + ']}'

        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}/forward'.format(self.message_id)

        self._make_api_call('post', endpoint=endpoint, data=payload)

    def reply(self, reply_comment):
        """Reply to the Message.

        Notes:
            HTML can be inserted in the string and will be interpreted properly by Outlook.

        Args:
            reply_comment: String message to send with email.

        """
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/reply'

        self._make_api_call('post', endpoint, data=payload)

    def reply_all(self, reply_comment):
        """Replies to everyone on the email, including those on the CC line.

        With great power, comes great responsibility.

        Args:
            reply_comment: The string comment to send to everyone on the email.

        """
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}/replyall'.format(self.message_id)

        self._make_api_call('post', endpoint, data=payload)

    def delete_message(self):
        """Deletes the email"""
        warnings.warn('delete_message() is deprecated and will be removed in v1.0. Use delete() instead.',
                      DeprecationWarning)
        self.delete()

    def delete(self):
        """Deletes the email"""
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id
        self._make_api_call('delete', endpoint)

    def _move_to(self, destination):
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/move'
        payload = '{ "DestinationId": "' + destination + '"}'
        self._make_api_call('post', endpoint, data=payload)

    def move_to_inbox(self):
        """Moves the email to the account's Inbox"""
        self._move_to('Inbox')

    def move_to_deleted(self):
        """Moves the email to the account's Deleted Items folder"""
        self._move_to('DeletedItems')

    def move_to_drafts(self):
        """Moves the email to the account's Drafts folder"""
        self._move_to('Drafts')

    def move_to(self, folder_id):
        """Moves the email to the folder specified by the folder_id.

        The folder id must match the id provided by Outlook.

        Args:
            folder_id: A string containing the folder ID the message should be moved to

        """
        self._move_to(folder_id)

    def _copy_to(self, destination):
        access_token = self.account.access_token
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/copy'
        payload = '{ "DestinationId": "{}"}'.format(destination)

        self._make_api_call('post', endpoint, extra_headers=headers, data=payload)

    def copy_to_inbox(self):
        """Copies Message to account's Inbox"""
        self._copy_to('Inbox')

    def copy_to_deleted(self):
        """Copies Message to account's Deleted Items folder"""
        self._copy_to('DeletedItems')

    def copy_to_drafts(self):
        """Copies Message to account's Drafts folder"""
        self._copy_to('Drafts')

    def copy_to(self, folder_id):
        """Copies the email to the folder specified by the folder_id.

        The folder id must match the id provided by Outlook.

        Args:
            folder_id: A string containing the folder ID the message should be copied to

        """
        self._copy_to(folder_id)

    @property
    def is_read(self):
        """ Set the 'Read' status of an email """
        return self.__is_read

    @is_read.setter
    def is_read(self, boolean):
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}'.format(self.message_id)
        payload = dict(IsRead=boolean)

        self._make_api_call('patch', endpoint, data=json.dumps(payload))
        self.__is_read = boolean

