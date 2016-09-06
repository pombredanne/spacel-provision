import unittest

from mock import patch
from spacel.aws.clients import ClientCache

REGION = 'us-east-1'


class TestClientCache(unittest.TestCase):
    def setUp(self):
        self.clients = ClientCache()

    @patch('spacel.aws.clients.boto3')
    def test_cloudformation(self, mock_boto3):
        self.clients.cloudformation(REGION)
        mock_boto3.client.assert_called_once_with('cloudformation', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_ec2(self, mock_boto3):
        self.clients.ec2(REGION)
        mock_boto3.client.assert_called_once_with('ec2', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_ec2_cached(self, mock_boto3):
        self.clients.ec2(REGION)
        self.clients.ec2(REGION)
        self.assertEqual(1, mock_boto3.client.call_count)

    @patch('spacel.aws.clients.boto3')
    def test_s3(self, mock_boto3):
        self.clients.s3(REGION)
        mock_boto3.resource.assert_called_once_with('s3', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_s3_cached(self, mock_boto3):
        self.clients.s3(REGION)
        self.clients.s3(REGION)
        self.assertEqual(1, mock_boto3.resource.call_count)