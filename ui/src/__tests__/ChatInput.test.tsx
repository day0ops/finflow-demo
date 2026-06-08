import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInput from "@/components/ChatInput";

describe("ChatInput", () => {
  it("calls onSend with typed message on Enter", async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);
    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "hello");
    await user.keyboard("{Enter}");
    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("does not send on Shift+Enter (newline)", async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);
    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "line1");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables send button when disabled=true", () => {
    render(<ChatInput onSend={() => {}} disabled={true} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
