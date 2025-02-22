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
  });
});
