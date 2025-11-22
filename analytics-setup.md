# Google Analytics Setup Guide

## Step 1: Create Google Analytics Account

1. Go to https://analytics.google.com/
2. Click "Start measuring" or "Admin" (gear icon)
3. Create an Account:
   - Account Name: `Soft Systems Studio`
4. Create a Property:
   - Property Name: `AI Agents Landing Page`
   - Time zone: Your timezone
   - Currency: USD
5. Configure Data Stream:
   - Platform: **Web**
   - Website URL: `https://ai-agents-ruddy.vercel.app`
   - Stream name: `Landing Page`
6. Copy your **Measurement ID** (looks like `G-XXXXXXXXXX`)

## Step 2: Add Measurement ID to Your Site

Replace `G-XXXXXXXXXX` in `index.html` with your actual Measurement ID:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-YOUR-ID-HERE"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-YOUR-ID-HERE');
</script>
```

**Location**: Lines 7-14 in `index.html` (right after the title tag)

## Step 3: Add to Vercel Environment Variables (Optional)

For better security, you can load the GA ID from environment variables:

1. In Vercel dashboard → Settings → Environment Variables
2. Add new variable:
   - Key: `GOOGLE_ANALYTICS_ID`
   - Value: `G-YOUR-ID-HERE`
3. Update `build.sh` to generate it:
   ```bash
   GOOGLE_ANALYTICS_ID: '${GOOGLE_ANALYTICS_ID:-G-XXXXXXXXXX}'
   ```

## Step 4: Deploy Changes

```bash
git add index.html
git commit -m "feat: Add Google Analytics tracking"
git push
```

Vercel will automatically redeploy (takes ~1-2 minutes).

## Step 5: Verify Tracking is Working

### Real-time Test:
1. Go to Google Analytics → Reports → Realtime
2. Open your site: https://ai-agents-ruddy.vercel.app
3. You should see yourself as an active user!

### Wait 24-48 hours for full reports to populate

## What We're Tracking

### Automatic Events (Google Analytics 4):
- ✅ **Page views** - Every time someone visits
- ✅ **Session start** - New visitor session
- ✅ **First visit** - First time user
- ✅ **Scroll depth** - How far down the page
- ✅ **Outbound clicks** - Links to external sites
- ✅ **File downloads** - If you add PDFs/files

### Custom Events We Added:
- ✅ **form_submission** - When contact form succeeds
  - Category: Contact
  - Label: Contact Form
  - Service: Which service they're interested in
  - Value: 1 (for conversion counting)

## Key Metrics to Monitor

### Acquisition:
- **Traffic sources**: Where visitors come from
  - Organic search (Google)
  - Direct (typed URL or bookmark)
  - Referral (other websites)
  - Social (Twitter, LinkedIn, etc.)

### Engagement:
- **Average engagement time**: How long people stay
- **Engaged sessions per user**: Quality of visits
- **Events per session**: Interaction level

### Conversions:
- **Form submissions**: Your most important metric!
- **Conversion rate**: Visitors → Leads %
- **Goal completions**: Track revenue when sales start

## Setting Up Conversions in GA4

1. Go to **Admin** → Property → **Events**
2. Click **Create event** → "Mark as conversion"
3. Check the box next to `form_submission`
4. Now it's tracked as a conversion!

## Recommended Reports to Check Weekly

1. **Realtime** - See current visitors
2. **Acquisition Overview** - Where traffic comes from
3. **Engagement → Pages and screens** - Most viewed pages
4. **Conversions** - Form submission count
5. **User attributes** - Demographics (age, location)

## Advanced: Set Up Goals & Funnels

### Goal: Get 5 form submissions per week

1. In GA4, go to **Admin** → **Custom definitions**
2. Create custom metrics for tracking:
   - Contact Form Starts (when form is focused)
   - Contact Form Completions (successful submission)
   - Conversion Rate = Completions / Page Views

### Funnel Analysis:
1. Page Load
2. Scroll to Contact Section
3. Form Start (click in field)
4. Form Submit
5. Success Message

This shows where people drop off!

## Troubleshooting

### "No data showing in GA4"
- Wait 24-48 hours for initial data
- Check Realtime report (instant)
- Verify Measurement ID is correct
- Check browser console for errors
- Make sure ad blockers are disabled for testing

### "Tracking code not found"
- View page source, search for "gtag"
- Should see Google Analytics script in `<head>`
- Redeploy if missing after push

### "Events not showing"
- Submit the form yourself
- Check Realtime → Events
- Look for `form_submission` event
- May take 5-10 minutes to appear

## Privacy Considerations

Google Analytics 4 is GDPR/CCPA compliant by default:
- ✅ No personally identifiable information (PII) tracked
- ✅ IP addresses anonymized
- ✅ Cookie consent not required for basic analytics (in most regions)

**Optional**: Add cookie consent banner if you want to be extra cautious:
- Use tools like CookieYes, Osano, or Termly
- Free tiers available

## Next Steps After Setup

1. **Share access** with team members:
   - Admin → Property Access Management
   - Add emails with Viewer or Editor role

2. **Set up email reports**:
   - Get weekly/monthly summaries delivered

3. **Connect to Google Search Console**:
   - See what keywords bring traffic
   - Find SEO opportunities

4. **Install GA4 Chrome extension**:
   - Quick access to reports
   - Realtime notifications

## Expected Results (First Week)

Based on typical landing page performance:

- **Traffic**: 0-50 visitors (organically, no ads yet)
- **Bounce rate**: 40-70% (normal for landing pages)
- **Form submissions**: 0-2 (conversion rate ~2-5%)
- **Avg. time on page**: 1-3 minutes

**To increase traffic:**
- Share on social media
- Post in relevant communities
- Start Google Ads campaign
- SEO optimization (titles, meta descriptions)

## Questions?

Check Google Analytics help: https://support.google.com/analytics/

---

**Status**: ✅ Tracking code added to `index.html`  
**Next**: Get your Measurement ID and replace `G-XXXXXXXXXX`
