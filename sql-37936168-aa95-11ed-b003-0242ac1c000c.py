import unittest
import requests
import json
import random

class TestProfile(unittest.TestCase):
    def test_add_user(self):
        for _ in range(3):
            string = ''.join([chr(random.randint(65, 90)) for _ in range(9)])
            data = {
                'first_name': string,
                'second_name': string,
                'login': string,
                'password': string,
            }
            print(data)
            resp = requests.post('http://127.0.0.1:5000/register', json=data)
            print(resp.text)
            response = json.loads(resp.text)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(response['status'], 1)
            print('/register test_add_user: {}'.format(resp.text))

    def test_b_get_user(self):
        resp = requests.get('http://127.0.0.1:5000/profiles')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.text)
        print('/profiles get_user: {}'.format(resp.text))
        users = json.loads(resp.text)
        for user in users:
            resp = requests.get('http://127.0.0.1:5000/profile/{}'.format(user['id']))
            response = json.loads(resp.text)
            print('/profile/{} get_user: {}'.format(user['id'], response))
            self.assertEqual(resp.status_code, 200)
            self.assertIsNotNone(resp.text)
            self.assertGreater(response['id'], 0)


    def test_c_login_user(self):
        resp = requests.get('http://127.0.0.1:5000/profiles')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.text)
        users = json.loads(resp.text)
        for user in users:
            if user['id'] != 191:
                data = {
                    'login': user['first_name'],
                    'password': user['first_name'],
                }
                resp = requests.post('http://127.0.0.1:5000/login', json=data)
                print('/login login_user: {}'.format(resp.text))
                self.assertEqual(resp.status_code, 200)
                self.assertGreater(user['id'], 0)
                self.assertIsNotNone(resp.text)


                data = {
                    'login': '',
                    'password': '',
                }
                resp = requests.post('http://127.0.0.1:5000/login', json=data)
                self.assertEqual(resp.status_code, 200)
                self.assertGreater(user['id'], 0)
                self.assertIsNotNone(resp.text)
                print('/login login_user: {}'.format(resp.text))

    def test_d_update_user(self):
        string = ''.join([chr(random.randint(33, 126)) for _ in range(9)])
        resp = requests.get('http://127.0.0.1:5000/profiles')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.text)
        users = json.loads(resp.text)
        for user in users:
            if user['id'] != 191:
                # Неизвестное поле. Менять можно только fist_name/second_name
                data = {
                    string: string,
                    string: string,
                }
                resp = requests.put('http://127.0.0.1:5000/profile/{}'.format(user['id']), json=data)
                response = json.loads(resp.text)
                print(response)
                self.assertEqual(resp.status_code, 200)
                self.assertIsNotNone(resp.text)
                self.assertEqual(response['status'], 0)
                self.assertIsNotNone(response['message'])
                print('[1] /profile/{} update_user: {}'.format(user['id'], resp.text))

                # 1 эквивалентное поле не было изменено
                resp = requests.get('http://127.0.0.1:5000/profile/{}'.format(user['id']), json=data)
                response = json.loads(resp.text)
                data = {
                    'first_name': response['first_name'],
                    'second_name': string,
                }
                resp = requests.put('http://127.0.0.1:5000/profile/{}'.format(user['id']), json=data)
                response2 = json.loads(resp.text)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(response2['status'], 1)
                self.assertIsNotNone(response2['message'])
                print('[2] /profile/{} update_user: {}'.format(user['id'], resp.text))

                # {'status': 1}
                data = {
                    'first_name': string + 'a',
                    'second_name': string + 'a',
                }
                resp = requests.put('http://127.0.0.1:5000/profile/{}'.format(user['id']), json=data)
                response = json.loads(resp.text)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(response['status'], 1)
                print('[3] /profile/{} update_user: {}'.format(user['id'], resp.text))


    def test_e_del_user(self):
        resp = requests.get('http://127.0.0.1:5000/profiles')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.text)
        users = json.loads(resp.text)
        for user in users:
            if user['id'] != 191:
                resp = requests.delete('http://127.0.0.1:5000/profile/{}'.format(user['id']))
                response = json.loads(resp.text)
                self.assertEqual(resp.status_code, 200)
                self.assertIsNotNone(resp.text)
                self.assertEqual(response['status'], 1)
                print('/profile/{} del_user: {}'.format(user['id'], resp.text))


if __name__ == '__main__':
    unittest.main()
