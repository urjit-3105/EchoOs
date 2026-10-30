# 🤝 Contributing to ECHO WorkforceOS

Thank you for your interest in contributing to **ECHO WorkforceOS**! This guide outlines our coding standards, branch conventions, testing practices, and pull request workflow.

---

## 🛠️ Development Setup

1. **Fork & Clone**: Fork the repository on GitHub and clone your fork locally.
2. **Branching Strategy**:
   - `main`: Production-ready branch.
   - `feature/feature-name`: Feature development.
   - `bugfix/issue-description`: Bug fixes.

---

## 🐍 Backend Guidelines (Python / FastAPI)

- Follow **PEP 8** style guidelines.
- Use explicit type annotations for function signatures and data models.
- Validate inputs using **Pydantic v2** models.
- Format code using Black/Ruff:
  ```bash
  black backend/
  ```

---

## ⚛️ Frontend Guidelines (Next.js / TypeScript)

- Use **TypeScript strict mode**.
- Use **TailwindCSS** for component styling.
- Ensure all API fetching uses custom React Query hooks under `src/hooks/`.
- Never put hardcoded API URLs in client code; consume `NEXT_PUBLIC_API_URL`.

---

## 🧪 Testing Guidelines

Before opening a pull request, run all unit and end-to-end scenario tests:

```bash
# Run backend test suite
cd backend
python3 -m pytest

# Run frontend build check
cd ../frontend
npm run build
```

All test cases must pass with 100% clean output.

---

## 📝 Pull Request Checklist

- [ ] Clear title following conventional commits (e.g. `feat: add Google Calendar refresh token handler`).
- [ ] Updated tests covering new functionality or bug fix.
- [ ] No secrets or hardcoded API keys committed.
- [ ] Project documentation updated if API endpoints or environment variables changed.
