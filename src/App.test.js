import { render, screen } from "@testing-library/react";
import App from "./App";

// Ensure `mediaDevices` exists and is mocked properly
beforeAll(() => {
  Object.defineProperty(global.navigator, "mediaDevices", {
    writable: true,
    value: {
      getUserMedia: jest.fn().mockImplementation(() =>
        Promise.resolve({
          getTracks: () => [
            {
              stop: jest.fn(),
            },
          ],
        })
      ),
    },
  });
});

test("renders real-time transcription header", async () => {
  render(<App />);
  const headerElement = await screen.findByText(/real-time transcription/i); // Match "Real-Time Transcription"
  expect(headerElement).toBeInTheDocument();
});
