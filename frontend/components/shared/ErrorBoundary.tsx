"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "./Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex min-h-dvh items-center justify-center bg-ground px-4">
          <div className="panel w-full max-w-md p-6">
            <p className="label-wire mb-2 text-bad">error</p>
            <h1 className="t-heading mb-2 text-ink">
              Something went wrong
            </h1>
            <p className="mb-6 text-ui text-muted">
              {this.state.error?.message ||
                "An unexpected error occurred while rendering this page."}
            </p>
            <Button
              onClick={() => {
                this.setState({ hasError: false, error: undefined });
                window.location.href = "/dashboard";
              }}
            >
              Back to the dashboard
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
