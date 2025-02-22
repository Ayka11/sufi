import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import { io } from 'socket.io-client'; // Import socket.io-client

// Mock socket.io-client and useState
jest.mock('socket.io-client');
jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useState: (initialState) => [initialState, jest.fn()],
}));

describe('App', () => {
  let mockSocket;

  beforeEach(() => {
    // Mock socket instance
    mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
    };

    // Mock socket.io-client to return the mock socket instance
    io.mockReturnValue(mockSocket);
  });

  test('renders without crashing', () => {
    render(<App />);

    // Check if the elements you expect to be present are rendered
    expect(screen.getByText(/Real-Time Transcription/i)).toBeInTheDocument();
    expect(screen.getByText(/Start Recording/i)).toBeInTheDocument();
    expect(screen.getByText(/Stop Recording/i)).toBeInTheDocument();
  });

  test('starts and stops recording', async () => {
    render(<App />);

    // Get the start and stop recording buttons
    const startButton = screen.getByText(/Start Recording/i);
    const stopButton = screen.getByText(/Stop Recording/i);

    // Initially, stop button should be disabled
    expect(stopButton).toBeDisabled();

    // Simulate a click on the start button
    fireEvent.click(startButton);

    // Wait for the stop button to be enabled
    await waitFor(() => expect(stopButton).not.toBeDisabled());

    // Simulate a click on the stop button
    fireEvent.click(stopButton);

    // Verify that after stopping, the start button is re-enabled
    expect(startButton).not.toBeDisabled();
  });
});
