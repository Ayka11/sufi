import { render, screen } from "@testing-library/react";
import App from "./App";

// Mock getUserMedia to prevent Jest from failing
beforeAll(() => {
  global.navigator.mediaDevices = {
    getUserMedia: jest.fn(() =>
      Promise.resolve({
        getTracks: () => [
          {
            stop: jest.fn(),
          },
        ],
      })
    ),
  };
});

test("renders real-time transcription header", () => {
  render(<App />);
  const headerElement = screen.getByText(/real-time transcription/i); // Match "Real-Time Transcription"
  expect(headerElement).toBeInTheDocument();
});
