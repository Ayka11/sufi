import { render, screen } from "@testing-library/react";
import App from "./App";

// Mock getUserMedia to prevent Jest from failing
beforeAll(() => {
  Object.defineProperty(global.navigator, "mediaDevices", {
    writable: true,
    value: {
      getUserMedia: jest.fn().mockResolvedValue({
        getTracks: () => [
          {
            stop: jest.fn(),
          },
        ],
      }),
    },
  });
});

test("renders real-time transcription header", () => {
  render(<App />);
  const headerElement = screen.getByText(/real-time transcription/i); // Match "Real-Time Transcription"
  expect(headerElement).toBeInTheDocument();
});
