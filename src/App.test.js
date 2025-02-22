// Updated App.test.js
import { render } from "@testing-library/react";
import App from "./App";

global.navigator.mediaDevices = {
  getUserMedia: jest.fn().mockResolvedValue({ getTracks: () => [] }),
};

test("renders without crashing", async () => {
  render(<App />);
  expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
});
