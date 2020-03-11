import unittest
import envoy

class SimpleTest(unittest.TestCase):

    def test_pipe(self):
        r = envoy.run("echo -n 'hi' | tr [:lower:] [:upper:]")
        self.assertEqual(r.std_out, "HI")
        self.assertEqual(r.status_code, 0)


class ConnectedCommandTest(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
