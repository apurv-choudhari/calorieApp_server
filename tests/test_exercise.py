import unittest
from application import app


class ExerciseFinderTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_valid_inputs(self):
        response = self.client.post(
            '/', data={'muscle': 'biceps', 'difficulty': 'beginner'})
        self.assertIn('Bicep Curl', response.data.decode())
        self.assertIn('Strength', response.data.decode())

    def test_empty_muscle_input(self):
        response = self.client.post(
            '/', data={'muscle': '', 'difficulty': 'beginner'})
        self.assertIn('Both muscle and difficulty are required!',
                      response.data.decode())

    def test_empty_difficulty_input(self):
        response = self.client.post(
            '/', data={'muscle': 'biceps', 'difficulty': ''})
        self.assertIn('Both muscle and difficulty are required!',
                      response.data.decode())

    def test_error_message_display(self):
        response = self.client.post(
            '/', data={'muscle': 'xyzmuscle', 'difficulty': 'intermediate'})
        self.assertIn(
            'No exercises found for the specified muscle and difficulty.', response.data.decode())

    def test_exercises_rendered(self):
        response = self.client.post(
            '/', data={'muscle': 'biceps', 'difficulty': 'beginner'})
        self.assertIn('Bicep Curl', response.data.decode())
        self.assertIn('Beginner', response.data.decode())
        self.assertIn('Dumbbell', response.data.decode())

    def test_multiple_exercises_rendered(self):
        response = self.client.post(
            '/', data={'muscle': 'triceps', 'difficulty': 'intermediate'})
        self.assertIn('Tricep Dips', response.data.decode())
        self.assertIn('Intermediate', response.data.decode())


if __name__ == '__main__':
    unittest.main()
