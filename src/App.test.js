import { render, screen } from "@testing-library/react";
import App from "./App";

beforeAll(() => {
  if (!global.navigator.mediaDevices) {
    global.navigator.mediaDevices = {};
  }

  global.navigator.mediaDevices.getUserMedia = jest.fn().mockResolvedValue({
    getTracks: () => [],
  });
});

test("renders without crashing", async () => {
  render(<App />);
  
  // Wait for the effect to resolve
  await expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
});
