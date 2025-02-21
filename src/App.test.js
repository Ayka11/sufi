// App.test.js
import { render, screen } from "@testing-library/react";
import App from "./App";

beforeAll(() => {
  global.navigator.mediaDevices = {
    getUserMedia: jest.fn().mockResolvedValue({
      // Mock a fake MediaStream
      getTracks: () => [],
    }),
  };
});

test("renders without crashing", () => {
  render(<App />);
  expect(screen.getByText(/some text from App/i)).toBeInTheDocument();
});
