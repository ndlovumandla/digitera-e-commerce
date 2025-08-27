# 🇿🇦 Digitera Platform

> **All-in-one platform for South African creators to sell digital products**

Digitera is a comprehensive Django-based e-commerce platform specifically designed for the South African market, featuring ZAR currency support, VAT compliance, local payment integrations, and creator-focused tools.

![Digitera Platform](https://img.shields.io/badge/Django-5.2.5-green) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![License](https://img.shields.io/badge/License-Proprietary-red)

## 🌟 Key Features

### 🛒 **E-commerce & Marketplace**
- **Product Management**: Digital downloads, courses, memberships, events, and communities
- **Shopping Cart & Checkout**: Full cart functionality with guest and user checkout
- **Order Management**: Complete order lifecycle with tracking and fulfillment
- **Payment Processing**: Integrated payment gateways with demo mode
- **Product Discovery**: Advanced search, filtering, and categorization

### 👥 **User Management & Authentication**
- **Multi-Role System**: Creators, Buyers, Admins, and Moderators
- **Role Switching**: Easy switching between creator and buyer modes
- **User Profiles**: Comprehensive profiles with South African specifics
- **Two-Factor Authentication (2FA)**: Enhanced security features
- **Social Authentication**: Google OAuth integration
- **Creator Onboarding**: Step-by-step creator signup and verification

### 🏪 **Creator Tools**
- **Storefront Management**: Custom creator storefronts with branding
- **Product Creation**: Multi-step product creation with media management
- **Analytics Dashboard**: Sales tracking, revenue analytics, and performance metrics
- **Creator Profiles**: Professional profiles with banking and branding details
- **Digital Asset Management**: Secure file hosting and delivery

### 💰 **South African Market Features**
- **ZAR Currency**: Native South African Rand support
- **VAT Compliance**: Automatic VAT calculation (15% standard rate)
- **Local Banking**: South African banking integration support
- **Regulatory Compliance**: POPIA and local business law compliance
- **Localized Content**: South African business templates and resources

### 🔒 **Security & Compliance**
- **Secure Downloads**: Time-limited and user-authenticated download links
- **Fraud Detection**: Built-in fraud monitoring and prevention
- **Data Protection**: GDPR/POPIA compliant data handling
- **Payment Security**: PCI-compliant payment processing
- **User Verification**: Email verification and identity checks

### 📊 **Analytics & Reporting**
- **Sales Analytics**: Revenue tracking, conversion metrics, and trends
- **User Analytics**: User behavior, session tracking, and engagement
- **Product Performance**: View counts, purchase rates, and ratings
- **Financial Reporting**: Tax reports, VAT summaries, and payout tracking

### 🎨 **Frontend & Design**
- **Responsive Design**: Bootstrap 5.3.0 + Tailwind CSS integration
- **Modern UI/UX**: Clean, professional South African-themed design
- **Mobile Optimized**: Full mobile responsiveness
- **Multi-language Ready**: i18n support for multiple languages

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **pip**

### Run the Website in 4 Commands

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database**
   ```bash
   python manage.py migrate
   ```

3. **Load sample data (optional)**
   ```bash
   python create_sample_data.py
   ```

4. **Start the server**
   ```bash
   python manage.py runserver
   ```

**🎉 That's it! Visit:** http://127.0.0.1:8000/

### Test Login
- **Creator**: `creator@example.com` / `testpass123`
- **Buyer**: `buyer@example.com` / `testpass123`
- **Admin**: `admin@example.com` / `testpass123`

## 🛠 Main Dependencies

```
Django 5.2.5          # Web framework
Bootstrap 5.3.0        # CSS framework  
SQLite                 # Database (built-in)
Stripe                 # Payments
Python 3.8+           # Programming language
```

*Full dependency list in `requirements.txt`*

## 📋 Common Commands

### Development
```bash
# Start server
python manage.py runserver

# Create admin user
python manage.py createsuperuser

# Reset database (if needed)
python manage.py flush
python manage.py migrate
python create_sample_data.py

# Make new migrations
python manage.py makemigrations
python manage.py migrate
```

### Troubleshooting
```bash
# If you get migration errors
python manage.py migrate --fake-initial

# If database is corrupted
del db.sqlite3
python manage.py migrate
python create_sample_data.py
```

## 🏗 Project Structure

```
Digitera/
├── accounts/          # Users & authentication
├── products/          # Product management  
├── orders/            # Shopping cart & orders
├── payments/          # Payment processing
├── storefronts/       # Creator stores
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── manage.py          # Django commands
└── requirements.txt   # Dependencies
```


## 👥 Test Users

```
Creators:     creator@example.com     | testpass123
Buyers:       buyer@example.com       | testpass123  
Admins:       admin@example.com       | testpass123
```

## 🧪 Quick Test

1. **Start server**: `python manage.py runserver`
2. **Login**: http://127.0.0.1:8000/accounts/login/ (use test accounts above)
3. **Browse products**: http://127.0.0.1:8000/products/marketplace/
4. **Buy something**: Add to cart → Checkout → Demo payment
5. **Create products**: Switch to creator role → Create new product

---

**Built for South African creators** 🇿🇦

*Need help? Check the additional `.md` files in the project folder.*
