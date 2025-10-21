# PayLab E2E Testing Setup with Playwright

## 🎉 **Setup Complete!**

Your PayLab project now has a complete Playwright E2E testing setup. Here's what was installed and configured:

## 📦 **What's Installed**

- **Node.js**: v24.3.0 ✅
- **npm**: v11.4.2 ✅  
- **Playwright**: v1.56.1 ✅
- **Browser Binaries**: Chromium, Firefox, WebKit, Mobile browsers ✅

## 📁 **Files Created**

```
paylab/
├── package.json              # Node.js project configuration
├── playwright.config.ts      # Playwright configuration
├── tests/e2e/
│   ├── basic.spec.ts         # Basic connectivity tests
│   └── payments_ui_invalid.spec.ts  # Comprehensive invalid data tests
└── node_modules/             # Dependencies
```

## 🧪 **Available Tests**

### **Basic Tests** (`tests/e2e/basic.spec.ts`)
- API health check
- Frontend page loading

### **Invalid Data Tests** (`tests/e2e/payments_ui_invalid.spec.ts`)
- Negative amount validation
- Zero amount validation  
- Empty order ID validation
- Extremely large amount handling
- Missing API key scenarios
- Invalid API key scenarios
- Network error handling
- UI state management

**Total: 70 tests** across 7 browser configurations

## 🚀 **How to Run Tests**

### **Prerequisites**
Make sure your FastAPI server is running:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **Run All Tests**
```bash
npm test
# or
npx playwright test
```

### **Run Specific Test File**
```bash
npx playwright test tests/e2e/basic.spec.ts
npx playwright test tests/e2e/payments_ui_invalid.spec.ts
```

### **Run Tests in Specific Browser**
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### **Run Tests with UI (Interactive Mode)**
```bash
npm run test:ui
# or
npx playwright test --ui
```

### **Run Tests in Headed Mode (See Browser)**
```bash
npm run test:headed
# or
npx playwright test --headed
```

### **Debug Tests**
```bash
npm run test:debug
# or
npx playwright test --debug
```

### **View Test Report**
```bash
npm run test:report
# or
npx playwright show-report
```

## 🔧 **Configuration**

### **Playwright Config** (`playwright.config.ts`)
- **Base URL**: http://localhost:8000
- **Test Directory**: ./tests/e2e
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari, Edge, Chrome
- **Auto-start server**: Configured to start FastAPI automatically
- **Screenshots**: On failure
- **Videos**: On failure
- **Traces**: On retry

### **Package.json Scripts**
```json
{
  "test": "playwright test",
  "test:ui": "playwright test --ui", 
  "test:headed": "playwright test --headed",
  "test:debug": "playwright test --debug",
  "test:report": "playwright show-report",
  "test:install": "playwright install"
}
```

## 🎯 **Test Scenarios Covered**

### **API Validation Tests**
- ✅ Negative amounts return 422 error
- ✅ Zero amounts return 422 error  
- ✅ Empty order IDs return 422 error
- ✅ Large amounts are handled properly
- ✅ Missing API keys return 401 error
- ✅ Invalid API keys return 401 error

### **UI Behavior Tests**
- ✅ Error styling is applied correctly
- ✅ Error messages are displayed
- ✅ Button states are managed properly
- ✅ Network errors are handled gracefully

### **Cross-Browser Testing**
- ✅ Desktop: Chrome, Firefox, Safari, Edge
- ✅ Mobile: Chrome, Safari
- ✅ Different screen sizes and viewports

## 🐛 **Troubleshooting**

### **Server Not Running**
If tests fail with connection errors:
```bash
# Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check if server is responding
curl http://localhost:8000/health
```

### **Browser Issues**
If browser binaries are missing:
```bash
npx playwright install
```

### **Port Conflicts**
If port 8000 is busy:
```bash
# Check what's using port 8000
netstat -an | findstr 8000

# Kill process if needed, then restart server
```

## 📊 **Why Playwright Installation Takes Time**

Playwright downloads large browser binaries:
- **Chromium**: ~149 MB
- **Firefox**: ~105 MB  
- **WebKit**: ~58 MB
- **Additional tools**: ~2 MB

**Total download**: ~314 MB + dependencies

This is normal and only happens once during setup.

## 🎉 **Next Steps**

1. **Run the basic tests** to verify everything works:
   ```bash
   npx playwright test tests/e2e/basic.spec.ts --project=chromium
   ```

2. **Run the full invalid data test suite**:
   ```bash
   npx playwright test tests/e2e/payments_ui_invalid.spec.ts --project=chromium
   ```

3. **Add more test scenarios** as needed for your specific requirements

4. **Integrate with CI/CD** by adding Playwright tests to your GitHub Actions workflow

Your E2E testing setup is now complete and ready to use! 🚀