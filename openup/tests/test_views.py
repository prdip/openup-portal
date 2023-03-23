
from openup.tests.test_setup import TestSetup


class RegisrationTest(TestSetup):

    def test_registration(self):

       
        res = self.client.post(self.register_url,self.user_data,content_type='application/x-www-form-urlencoded')

    
        # self.assertEqual(self.user_data)

        # import pdb
        # pdb.set_trace()

      
        # self.assertEqual(res.data['user_first_name'])
       
