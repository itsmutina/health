# Mental Health Journal - Render Deployment Guide

This guide will help you deploy your Mental Health Journal application to Render.

## Prerequisites

1. A GitHub account
2. A Render account (sign up at https://render.com)
3. Your code pushed to a GitHub repository

## Step 1: Prepare Your Repository

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

## Step 2: Deploy to Render

### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to deploy

### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `mental-health-journal`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install --upgrade pip
     pip install -r requirements.txt
     python manage.py collectstatic --noinput
     python manage.py migrate
     ```
   - **Start Command**: `gunicorn mental_health_journal.wsgi:application`

## Step 3: Configure Environment Variables

In your Render service settings, add these environment variables:

### Required Variables:
- `DEBUG`: `False`
- `SECRET_KEY`: (Generate a secure secret key)
- `ALLOWED_HOSTS`: `your-app-name.onrender.com`
- `DATABASE_URL`: (Will be provided by Render PostgreSQL)

### Optional Variables:
- `EMAIL_HOST_USER`: Your email for sending password reset emails
- `EMAIL_HOST_PASSWORD`: Your email password or app password
- `DEFAULT_FROM_EMAIL`: `noreply@yourdomain.com`

## Step 4: Set Up PostgreSQL Database

1. In Render Dashboard, click "New +" and select "PostgreSQL"
2. Name it `mental-health-db`
3. Choose the Free plan
4. Copy the connection string to your web service's `DATABASE_URL` environment variable

## Step 5: Configure Email (Optional)

For password reset functionality, configure email settings:

1. **Gmail Setup**:
   - Enable 2-factor authentication
   - Generate an App Password
   - Use your Gmail address and app password

2. **Other Email Providers**:
   - Update `EMAIL_HOST` and `EMAIL_PORT` accordingly

## Step 6: Deploy

1. Click "Deploy" in your Render service
2. Wait for the build to complete
3. Your app will be available at `https://your-app-name.onrender.com`

## Step 7: Create Admin User

After deployment, create a superuser:

1. Go to your app's URL + `/admin/`
2. Or use Render's shell feature:
   ```bash
   python manage.py createsuperuser
   ```

## Troubleshooting

### Common Issues:

1. **Static Files Not Loading**:
   - Ensure `STATIC_ROOT` is set correctly
   - Check that `collectstatic` runs during build

2. **Database Connection Issues**:
   - Verify `DATABASE_URL` is set correctly
   - Check PostgreSQL service is running

3. **Email Not Working**:
   - Verify email credentials
   - Check email provider settings

4. **Build Failures**:
   - Check build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`

### Logs and Debugging:

- View logs in Render Dashboard under "Logs" tab
- Check build logs for deployment issues
- Monitor application logs for runtime errors

## Security Considerations

1. **Never commit sensitive data** to your repository
2. **Use environment variables** for secrets
3. **Enable HTTPS** (automatic on Render)
4. **Regularly update dependencies**

## Monitoring

- Monitor your app's performance in Render Dashboard
- Set up alerts for downtime
- Monitor database usage and performance

## Scaling

- Upgrade to paid plans for better performance
- Use Redis for caching in production
- Consider CDN for static files

## Support

- Render Documentation: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- Mental Health Journal Issues: Create an issue in your repository

---

Your Mental Health Journal application should now be live on Render! 🚀
