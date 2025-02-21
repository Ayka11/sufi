import { render, screen } from "@testing-library/react";
import App from "./App";

beforeAll(() => {
  // Ensure navigator.mediaDevices is defined
  if (!global.navigator.mediaDevices) {
    global.navigator.mediaDevices = {};
  }

  // Mock getUserMedia
  global.navigator.mediaDevices.getUserMedia = jest.fn().mockResolvedValue({
    getTracks: () => [],
  });
});

test("renders without crashing", async () => {
  render(<App />);
  
  // Wait for the effect to resolve
  await expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
});
