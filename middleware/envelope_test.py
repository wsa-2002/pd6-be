import unittest

from . import envelope


class TestEnveloped(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        ...

    async def test_happy_flow_normal(self):
        @envelope.enveloped
        async def dummy():
            return 123

        result = await dummy()
        self.assertEqual(result, {
            'success': True,
            'data': 123,
            'error': None,
        })

    async def test_happy_flow_exception(self):
        @envelope.enveloped
        async def dummy():
            raise Exception('expected exception for testing')

        result = await dummy()
        self.assertEqual(result, {
            'success': False,
            'data': None,
            'error': 'SystemException',
        })
