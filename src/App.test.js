import { render, screen, fireEvent } from "@testing-library/react";
import App from "./App";

// Mock navigator.mediaDevices.getUserMedia and MediaRecorder globally
beforeAll(() => {
  // Mock getUserMedia to return a mock stream
  global.navigator.mediaDevices = {
    getUserMedia: jest.fn().mockResolvedValue({
      getTracks: jest.fn(),
    }),
  };

  // Mock MediaRecorder to prevent actual recording logic
  global.MediaRecorder = jest.fn(() => ({
    start: jest.fn(),
    stop: jest.fn(),
    ondataavailable: jest.fn(),
    onstop: jest.fn(),
  }));
});

describe("App Component", () => {
  test("renders without crashing", () => {
    render(<App />);
    expect(screen.getByText(/Real-Time Transcription/i)).toBeInTheDocument();
  });

  test("start recording button enables when not recording", () => {
    render(<App />);
    const startButton = screen.getByRole("button", { name: /Start Recording/i });
    expect(startButton).not.toBeDisabled();
  });

  test("stop recording button enables when recording", () => {
    render(<App />);
    const startButton = screen.getByRole("button", { name: /Start Recording/i });
    fireEvent.click(startButton);

    const stopButton = screen.getByRole("button", { name: /Stop Recording/i });
    expect(stopButton).not.toBeDisabled();
  });

  test("should call getUserMedia once when the component mounts", () => {
    render(<App />);
    // Check if getUserMedia was called once on component mount
    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledTimes(1);
  });
});
