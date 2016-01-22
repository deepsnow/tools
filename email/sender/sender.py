import smtplib
##from email.mime.text import MIMEText
import email.mime.text
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import sys
import os.path
import configparser

import unittest
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import MagicMock
import io

## See http://kutuma.blogspot.com/2007/08/sending-emails-via-gmail-with-python.html for the inspiration on sending to a gmail account using another gmail account to authorize...

class EmailSender:
    '''
    This classs should be a Singleton. See http://www.python.org/workshops/1997-10/proceedings/savikko.html if you want to enforce this.
    '''

    def __init__( self ):
        self.msg = MIMEMultipart()
        self.to_addrs = []
        self.password = ''

    def ReadConfig(self):
        cp = configparser.ConfigParser()
        cp.read('config.ini')
        cpdef = cp['DEFAULT']
        self.msg['From'] = cpdef['from_addr']
        self.msg.preamble = cpdef['preamble']
        self.msg.epilogue = cpdef['epilogue']
        self.msg['Subject'] = cpdef['subject']
        self.password = cpdef['password']

    # Pass 't' to add a text file, and 'b' to add a binary file.
    def AttachFile( self, file_path, file_type ):
        if file_type == "t":
            attachment = self._ReadTextFileAsMime(file_path)
        elif file_type == "b":
            attachment = MIMEBase( "application", "octet_stream" )
            attach_handle = open( file_path, "rb" )
            attachment.set_payload( attach_handle.read() )
            attachment.add_header( "Content-Disposition", "attachment", filename=os.path.basename( file_path ) )
        else:
            raise TypeError("Invalid type parameter \"" + file_type + "\" was received.")
        attach_handle.close()
        self.msg.attach( attachment )

    def _ReadTextFileAsMime( self, file_path ):
        attach_handle = open( file_path, "r" )
        return email.mime.text.MIMEText( attach_handle.read() )

    # Always set the body before adding any attachements.
    def SetBody( self ):        
        body = self._ReadTextFileAsMime('body.txt')
        self.msg.attach( body )

    # Append additional recipients to the recipients list.
    def AddRecipients( self, recip_list ):
        self.to_addrs = self.to_addrs + recip_list

    def SendMessage( self ):
        try:
            self.msg['To'] = ", ".join( self.to_addrs )
            server = smtplib.SMTP( server_name, server_port )
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.msg['From'], self.password)
            server.sendmail( self.msg['From'], self.to_addrs, self.msg.as_string() )
            server.quit()
        except:
            raise RuntimeError(str(sys.exc_info()[0]))

class EmailSenderTest(unittest.TestCase):
    
    def setUp(self):
        self.es = EmailSender()

    def CpDefSimulator(self, name):
        if name == 'from_addr':
            return 'fa'
        elif name == 'preamble':
            return 'p'
        elif name == 'epilogue':
            return 'e'
        elif name == 'subject':
            return 's'
        elif name == 'password':
            return 'pswd'
        else:
            assert False

    def test_ReadConfig_ReadFileAndExtractSettingsSucceeds(self):
        assert self.es.msg['From'] != 'fa'
        assert self.es.msg.preamble != 'p'
        assert self.es.msg.epilogue != 'e'
        assert self.es.msg['Subject'] != 's'
        assert self.es.password != 'pswd'
        cp = MagicMock(spec=configparser.ConfigParser)
        cp['DEFAULT'] = MagicMock(spec=dict)
        cp['DEFAULT'].__getitem__.side_effect = self.CpDefSimulator
        with patch.object(configparser, 'ConfigParser', return_value=cp) as m1:
            self.es.ReadConfig()
        m1.assert_called_once()
        cp.read.assert_called_once_with('config.ini')
        assert self.es.msg['From'] == 'fa'
        assert self.es.msg.preamble == 'p'
        assert self.es.msg.epilogue == 'e'
        assert self.es.msg['Subject'] == 's'
        assert self.es.password == 'pswd'
        
    def test_SetBody_ReadFileAsMimeAndAttachToMsg(self):
        text = 'some mime text'
        file_handle = MagicMock(spec=io.TextIOBase)
        file_handle.read = MagicMock(return_value=text)
        mockOpen = MagicMock(return_value=file_handle)
        mockMimeText = MagicMock(return_value=text, spec=email.mime.text.MIMEText)
        with patch('builtins.open', mockOpen):
            with patch('email.mime.text.MIMEText', mockMimeText):
                self.es.SetBody()
        mockMimeText.assert_called_once_with(text)
        file_handle.read.assert_called_once()
