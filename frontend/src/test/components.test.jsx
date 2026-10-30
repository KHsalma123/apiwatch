import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import ConfirmDialog from "../components/ConfirmDialog";
import ProtectedRoute from "../components/ProtectedRoute";
import StatusBadge from "../components/StatusBadge";

vi.mock("../context/AuthContext", () => ({ useAuth: vi.fn() }));
import { useAuth } from "../context/AuthContext";

describe("StatusBadge", () => {
  it("shows a text label, not only a color", () => {
    render(<StatusBadge status="DOWN" />);
    expect(screen.getByText("Down")).toBeInTheDocument();
  });
  it("shows Paused for inactive monitors", () => {
    render(<StatusBadge status="UP" paused />);
    expect(screen.getByText("Paused")).toBeInTheDocument();
  });
});

describe("ProtectedRoute", () => {
  const renderAt = () =>
    render(
      <MemoryRouter initialEntries={["/secret"]}>
        <Routes>
          <Route path="/login" element={<p>Login page</p>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/secret" element={<p>Secret page</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

  it("redirects anonymous visitors to /login", () => {
    useAuth.mockReturnValue({ isAuthenticated: false, loading: false });
    renderAt();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });
  it("renders the page for authenticated users", () => {
    useAuth.mockReturnValue({ isAuthenticated: true, loading: false });
    renderAt();
    expect(screen.getByText("Secret page")).toBeInTheDocument();
  });
});

describe("ConfirmDialog", () => {
  it("calls onConfirm and onCancel", async () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(<ConfirmDialog open title="Delete?" message="Sure?" onConfirm={onConfirm} onCancel={onCancel} />);
    await userEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(onConfirm).toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalled();
  });
  it("renders nothing when closed", () => {
    render(<ConfirmDialog open={false} title="x" message="y" onConfirm={() => {}} onCancel={() => {}} />);
    expect(screen.queryByRole("alertdialog")).toBeNull();
  });
});
