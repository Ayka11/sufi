import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';
import { io } from 'socket.io-client'; // Import socket.io-client

// Mock socket.io-client
jest.mock('socket.io-client');

describe('App', () => {
  let mockSocket;

  beforeEach(() => {
    // Create a mock socket instance
    mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
    };

    // Mock the socket.io-client to return the mock socket instance
    io.mockReturnValue(mockSocket);
  });

  test('renders without crashing', () => {
    render(<App />);
    
    // Check if the elements you expect to be present are rendered
    expect(screen.getByText(/Real-Time Transcription/i)).toBeInTheDocument();
    expect(screen.getByText(/Start Recording/i)).toBeInTheDocument();
    expect(screen.getByText(/Stop Recording/i)).toBeInTheDocument();
  });

  test('starts and stops recording', () => {
    render(<App />);

    // Get the start and stop recording buttons
    const startButton = screen.getByText(/Start Recording/i);
    const stopButton = screen.getByText(/Stop Recording/i);

    // Check that the start button is enabled initially
    expect(startButton).not.toBeDisabled();

    // Simulate a click on the start button
    fireEvent.click(startButton);

    // Check that the stop button is enabled after starting the recording
    expect(stopButton).not.toBeDisabled();

    // Simulate a click on the stop button
    fireEvent.click(stopButton);

    // Check that the start button is re-enabled after stopping the recording
    expect(startButton).not.toBeDisabled();
  });
});
