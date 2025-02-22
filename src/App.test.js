
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
=======
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import App from './App';
import { io } from 'socket.io-client';

// Mock socket.io
jest.mock('socket.io-client', () => ({
  io: jest.fn().mockReturnValue({
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
  }),
}));

// Mocking fetch for sending audio to backend
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ transcription: 'This is a test transcription.' }),
  })
);

describe('App Component', () => {
  it('renders the component with initial elements', () => {
    render(<App />);
    
    expect(screen.getByText(/Real-Time Transcription/i)).toBeInTheDocument();
    expect(screen.getByText(/Language:/i)).toBeInTheDocument();
    expect(screen.getByText(/Service:/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Start Recording/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Stop Recording/i })).toBeInTheDocument();
  });

  it('starts and stops recording', async () => {
    render(<App />);

    const startButton = screen.getByRole('button', { name: /Start Recording/i });
    const stopButton = screen.getByRole('button', { name: /Stop Recording/i });

    fireEvent.click(startButton);
    expect(startButton).toBeDisabled();
    expect(stopButton).toBeEnabled();

    // Simulate stopping the recording after some time
    act(() => {
      fireEvent.click(stopButton);
    });

    expect(startButton).toBeEnabled();
    expect(stopButton).toBeDisabled();
  });

  it('sends audio to backend after stopping the recording', async () => {
    render(<App />);

    const startButton = screen.getByRole('button', { name: /Start Recording/i });
    const stopButton = screen.getByRole('button', { name: /Stop Recording/i });

    fireEvent.click(startButton);
    expect(global.fetch).not.toHaveBeenCalled();

    act(() => {
      fireEvent.click(stopButton);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith(
        'https://transkripsiya-backend.azurewebsites.net/upload_audio',
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  it('displays transcriptions received from the backend', async () => {
    render(<App />);

    const startButton = screen.getByRole('button', { name: /Start Recording/i });
    const stopButton = screen.getByRole('button', { name: /Stop Recording/i });

    fireEvent.click(startButton);
    act(() => {
      fireEvent.click(stopButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/This is a test transcription./i)).toBeInTheDocument();
    });
  });

  it('handles language change', () => {
    render(<App />);

    const languageSelect = screen.getByLabelText(/Language:/i);
    fireEvent.change(languageSelect, { target: { value: 'es-ES' } });
    expect(languageSelect.value).toBe('es-ES');
  });

  it('handles service change', () => {
    render(<App />);

    const serviceSelect = screen.getByLabelText(/Service:/i);
    fireEvent.change(serviceSelect, { target: { value: 'google' } });
    expect(serviceSelect.value).toBe('google');
  });

  it('saves and loads transcriptions from localStorage', () => {
    // Simulate previous transcription data in localStorage
    const initialTranscriptions = [
      { timestamp: '2025-02-22 12:00:00', text: 'Test transcription 1' },
    ];
    localStorage.setItem('transcriptions', JSON.stringify(initialTranscriptions));

    render(<App />);

    // Check if previous transcriptions are rendered
    expect(screen.getByText('2025-02-22 12:00:00: Test transcription 1')).toBeInTheDocument();
>>>>>>> 689825bd0aca3d464f58670c13a79271b91c09b8
  });
});
