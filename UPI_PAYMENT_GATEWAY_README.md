# UPI Payment Gateway for Trading Vault

A comprehensive UPI payment gateway system with QR code generation, payment tracking, and Discord bot integration. Deployed on Render for reliable hosting.

## Features

- 💳 **UPI Payment Processing**: Accept payments via UPI (GPay, PhonePe, Paytm)
- 📱 **QR Code Generation**: Automatic QR code generation for easy payments
- 📊 **Payment Dashboard**: Web dashboard for managing and verifying payments
- 🔐 **Secure Authentication**: Admin-only access to payment management
- 🤖 **Discord Integration**: Seamless integration with your existing Discord bot
- 💾 **Database Tracking**: SQLite database for payment history and tracking
- ✅ **Payment Verification**: Manual verification system with transaction IDs
- 🚀 **Render Deployment**: Ready-to-deploy on Render platform

## System Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Discord Bot   │────────▶│  Payment Gateway │◀────────│   Admin Panel   │
│   (ticket_bot)  │         │   (Flask App)    │         │   (Dashboard)   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │   SQLite DB  │
                              │  (payments)  │
                              └──────────────┘
```

## Prerequisites

- Python 3.8+
- Render account (free tier available)
- UPI ID (e.g., yourname@upi)
- Discord bot token (for integration)

## Local Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.payment.example` to `.env`:

```bash
cp .env.payment.example .env
```

Edit `.env` with your values:

```env
FLASK_SECRET_KEY=your_random_secret_key_here
WEB_USERNAME=admin
WEB_PASSWORD=your_secure_password_here
UPI_ID=yourname@upi
UPI_NAME=Trading Vault
UPI_MERCHANT_CODE=
DISCORD_TOKEN=your_discord_bot_token
PAYMENT_GATEWAY_URL=http://localhost:5001
```

### 3. Run Locally

```bash
python upi_payment_gateway.py
```

The payment gateway will be available at: `http://localhost:5001`

## Render Deployment

### 1. Prepare Your Code

Ensure all files are in your repository:
- `upi_payment_gateway.py`
- `upi_discord_integration.py`
- `render.yaml`
- `requirements.txt`
- `templates/` directory with all HTML files

### 2. Push to GitHub

```bash
git add .
git commit -m "Add UPI payment gateway"
git push origin main
```

### 3. Deploy on Render

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Review and configure environment variables:
   - `WEB_USERNAME`: Your admin username
   - `WEB_PASSWORD`: Your admin password
   - `UPI_ID`: Your UPI ID (e.g., yourname@upi)
   - `UPI_NAME`: Your merchant name
   - `UPI_MERCHANT_CODE`: (optional) Merchant code
   - `DISCORD_TOKEN`: Your Discord bot token

6. Click "Deploy Web Service"

### 4. Get Your Render URL

After deployment, Render will provide a URL like:
```
https://your-app-name.onrender.com
```

Update your `.env` file:
```env
PAYMENT_GATEWAY_URL=https://your-app-name.onrender.com
```

## Discord Bot Integration

### 1. Add Integration to Your Bot

In `ticket_bot.py`, add:

```python
# Import UPI integration
from upi_discord_integration import setup_upi_integration

# In setup_hook or after bot initialization
async def setup_hook(self):
    # ... existing setup code ...
    
    # Setup UPI payment integration
    setup_upi_integration(self)
```

### 2. New Commands Available

After integration, users can use:

- `/upipayment` - Create a new UPI payment
- `/paymentstatus` - Check payment status

### 3. Payment Flow

1. User opens a purchase ticket
2. Staff or user clicks "Create UPI Payment"
3. Payment link is generated with QR code
4. User scans QR code or clicks UPI link
5. User completes payment via UPI app
6. Admin verifies payment in dashboard
7. Payment status updates automatically

## Admin Dashboard

### Access Dashboard

1. Go to `https://your-app-name.onrender.com`
2. Login with your admin credentials
3. View payment statistics and recent payments

### Dashboard Features

- **Payment Statistics**: Total payments, pending, verified, revenue
- **Payment List**: View all payments with status
- **Verify Payments**: Mark payments as verified with transaction ID
- **Reject Payments**: Reject invalid payments with reason
- **Payment Settings**: Configure UPI ID, limits, etc.

### Verification Process

1. User completes UPI payment
2. Admin checks bank/UPI app for transaction
3. Admin enters transaction ID in dashboard
4. Payment marked as verified
5. User can see updated status on payment page

## API Endpoints

### Create Payment
```http
POST /api/create_payment
Content-Type: application/json

{
  "order_id": "CAPE-001",
  "user_id": 123456789,
  "user_name": "John Doe",
  "amount": 100.00,
  "currency": "INR",
  "notes": "Optional notes"
}
```

### Get Payment Status
```http
GET /api/payment/{payment_id}
```

### Verify Payment (Admin)
```http
POST /api/verify_payment
Content-Type: application/json

{
  "payment_id": "PAY2024...",
  "upi_transaction_id": "TXN123...",
  "verified_by": 1,
  "notes": "Optional notes"
}
```

### Reject Payment (Admin)
```http
POST /api/reject_payment
Content-Type: application/json

{
  "payment_id": "PAY2024...",
  "notes": "Reason for rejection"
}
```

### Get All Payments (Admin)
```http
GET /api/payments?status=pending&limit=50&offset=0
```

## Payment Page

Users can access their payment page via:
```
https://your-app-name.onrender.com/payment/{payment_id}
```

Features:
- QR code display
- UPI link for direct payment
- Payment instructions
- Real-time status updates
- Mobile-friendly design

## Security Features

- 🔐 Admin authentication required for dashboard
- 🛡️ Session management
- 🔒 SQL injection prevention (parameterized queries)
- ✅ Payment verification before completion
- 📝 Transaction ID tracking
- 🚫 Duplicate payment prevention

## Database Schema

### Payments Table
```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id TEXT UNIQUE NOT NULL,
    order_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    status TEXT DEFAULT 'pending',
    upi_transaction_id TEXT,
    screenshot_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    verified_by INTEGER,
    notes TEXT
);
```

### Payment Settings Table
```sql
CREATE TABLE payment_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upi_id TEXT NOT NULL,
    upi_name TEXT NOT NULL,
    merchant_code TEXT,
    min_amount REAL DEFAULT 1,
    max_amount REAL DEFAULT 100000,
    auto_verify BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

### Deployment Issues

**Build fails on Render:**
- Check `requirements.txt` includes all dependencies
- Ensure `render.yaml` is properly formatted
- Verify Python version compatibility

**Environment variables not loading:**
- Ensure variables are set in Render dashboard
- Check variable names match exactly
- Restart the service after adding variables

### Payment Issues

**QR code not generating:**
- Verify `qrcode` and `Pillow` packages are installed
- Check UPI ID format (must be valid email format)
- Ensure payment amount is within limits

**Payment verification failing:**
- Check database permissions
- Verify admin authentication
- Ensure payment ID exists in database

### Discord Integration Issues

**Bot not connecting to payment gateway:**
- Verify `PAYMENT_GATEWAY_URL` is correct
- Check if Render service is running
- Ensure firewall allows connections
- Test API endpoint manually

**Commands not registering:**
- Ensure integration is properly set up in `ticket_bot.py`
- Check bot has proper permissions
- Verify slash commands are synced

## Monitoring

### Render Dashboard

Monitor your deployment through Render's dashboard:
- CPU usage
- Memory usage
- Response times
- Error logs
- Deployment history

### Database Backup

The SQLite database (`payments.db`) is stored in the Render filesystem. For production use:

1. Set up regular backups via Render's disk feature
2. Or migrate to PostgreSQL for better reliability
3. Export database regularly:

```bash
sqlite3 payments.db .dump > backup.sql
```

## Scaling

For high-volume payments:

1. **Upgrade to PostgreSQL**: Replace SQLite with PostgreSQL
2. **Add Redis**: For caching and session management
3. **Load Balancing**: Use Render's load balancer
4. **CDN**: Serve static assets via CDN
5. **Monitoring**: Add application monitoring (Sentry, etc.)

## Cost

**Render Free Tier:**
- 512 MB RAM
- 0.1 CPU
- 750 hours/month
- Suitable for development/testing

**Render Starter ($7/month):**
- 512 MB RAM
- 0.5 CPU
- Always-on
- Better for production

## Future Enhancements

- [ ] Automatic payment verification via UPI APIs
- [ ] Webhook notifications for payment status
- [ ] Multiple payment methods (credit cards, etc.)
- [ ] Refund system
- [ ] Payment analytics and reports
- [ ] Multi-currency support
- [ ] Subscription/billing system
- [ ] Mobile app integration

## Support

For issues or questions:
1. Check this documentation
2. Review Render logs
3. Test API endpoints manually
4. Check Discord bot integration

## License

This payment gateway is part of the Trading Vault project.
