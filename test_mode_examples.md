# Test Mode Usage Examples

## Normal Operation (Default)
```bash
python src/orders/poller/main.py
```
This will use the default query `'is:unread'` to fetch all unread emails.

## Test Mode with Specific Invoice Emails
```bash
TEST_MODE=true TEST_EMAIL_QUERY="from:invoice@company.com OR subject:invoice" python src/orders/poller/main.py
```

## Test Mode Examples

### Test emails from specific sender
```bash
TEST_MODE=true TEST_EMAIL_QUERY="from:specific-sender@example.com" python src/orders/poller/main.py
```

### Test emails containing invoice keywords
```bash
TEST_MODE=true TEST_EMAIL_QUERY="subject:invoice OR subject:factura OR subject:\"invoice number\"" python src/orders/poller/main.py
```

### Test emails from multiple senders
```bash
TEST_MODE=true TEST_EMAIL_QUERY="from:sender1@company.com OR from:sender2@company.com" python src/orders/poller/main.py
```

### Test emails with specific content
```bash
TEST_MODE=true TEST_EMAIL_QUERY="\"logistics\" OR \"transport\" OR \"shipment\"" python src/orders/poller/main.py
```

### Test recent emails (last 7 days)
```bash
TEST_MODE=true TEST_EMAIL_QUERY="newer_than:7d" python src/orders/poller/main.py
```

## Notes
- When `TEST_MODE=true` but no `TEST_EMAIL_QUERY` is provided, the system will fall back to the default `'is:unread'` query
- The rest of the pipeline processing remains exactly the same in both modes
- All emails processed will go through the same classification, extraction, geocoding, and database save steps