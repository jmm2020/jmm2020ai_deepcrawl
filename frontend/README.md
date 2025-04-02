# Crawl4AI Frontend

This directory contains the Next.js frontend application for the Crawl4AI project.

## Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm run dev -- -p 3112
   ```

## Structure

- `src/app/` - Next.js app directory with pages and routes
- `src/components/` - Reusable React components
- `src/lib/` - Utility libraries and API clients
- `src/utils/` - Helper utilities
- `public/` - Static assets

## Environment Variables

The `.env.local` file contains the following configuration:
- `NEXT_PUBLIC_API_SERVER_URL` - URL for the API server (http://localhost:1111)

## Dependencies

This frontend uses:
- Next.js 13+ (App Router)
- Tailwind CSS for styling
- React for UI components 