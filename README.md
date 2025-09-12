# Mental Health Journal

A Django-based web application for tracking mental health, mood patterns, and personal insights.

## Features

- **Daily Mood Tracking**: Simple 0-10 mood scale with optional stress and sleep tracking
- **Emotion & Activity Tags**: Customizable tags for emotions and activities
- **Smart Insights**: AI-powered pattern recognition and correlations
- **Privacy-First**: Encrypted data storage with no social features
- **Reports & Export**: Generate PDF reports and export data
- **Reminder System**: Email reminders for daily logging
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Database**
   ```bash
   python manage.py migrate
   python manage.py setup_default_data
   ```

3. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

5. **Access the Application**
   - Landing page: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/
   - App: http://localhost:8000/app/

## Project Structure

```
mental_health_journal/
├── accounts/          # User management and settings
├── journal/           # Main journal functionality
├── insights/          # Analytics and pattern recognition
├── reports/           # PDF generation and sharing
├── templates/         # HTML templates
├── static/           # CSS, JS, and media files
└── mental_health_journal/  # Django project settings
```

## Key Models

- **User**: Custom user model with email authentication
- **JournalEntry**: Daily mood and activity entries
- **EmotionTag/ActivityTag**: Predefined tags for emotions and activities
- **UserSettings**: User preferences and reminder settings
- **Insight**: Generated insights and correlations
- **Report**: PDF reports with sharing capabilities

## Environment Variables

Create a `.env` file with:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Features in Detail

### 1. Landing Page
- Clean, calming design
- Clear value proposition
- Crisis resources prominently displayed

### 2. Onboarding
- 3-step setup process
- Reminder time selection
- Emotion and activity tag customization

### 3. Daily Logging
- Mood slider (0-10)
- Emotion chips (multi-select)
- Optional stress and sleep tracking
- Activity selection
- Daily prompts
- Free text notes

### 4. Dashboard
- 7-day mood trend chart
- Statistics cards (streak, average, etc.)
- Recent entries list
- Quick actions

### 5. Insights
- Mood trend analysis
- Correlation detection
- Pattern recognition
- Personalized recommendations

### 6. Reports
- PDF generation
- Shareable links (expiring)
- Date range selection
- Export capabilities

### 7. Settings
- Profile management
- Reminder preferences
- Tag customization
- Data export/deletion
- Privacy controls

## Security & Privacy

- Data encrypted at rest and in transit
- No social features or data sharing
- User controls all data export/deletion
- GDPR compliant
- Crisis resources always visible

## Deployment

The application is ready for deployment on platforms like:
- Heroku
- DigitalOcean
- AWS
- Google Cloud Platform

Make sure to:
1. Set `DEBUG=False` in production
2. Configure proper email backend
3. Set up Redis for Celery
4. Configure static file serving
5. Set up SSL/HTTPS

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please contact [your-email@example.com]

## Crisis Resources

**This is not a medical device.** If you're in crisis, please seek help immediately:

- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- Emergency Services: 911
