import { render, screen } from '@testing-library/react';
import App from './App';

test('renders real-time transcription header', () => {
  render(<App />);
  const headerElement = screen.getByText(/Real-Time Transcription/i);
  expect(headerElement).toBeInTheDocument();
});

