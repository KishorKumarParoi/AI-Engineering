# Job Application Tracker — Quick Start

## Running the App

```bash
npm install          # Already done
npx prisma db push  # Create database (already done)
npm run dev         # Start dev server
```

Then open **http://localhost:3000** in your browser.

## Features

### 📋 Kanban Board
- **7 Columns**: Wishlist → Applied → Phone Screen → Interviewing → Offer → Rejected → Withdrawn
- **Drag & Drop**: Grab any card to move it between columns (the card will become semi-transparent while dragging)
- Visual feedback: Columns highlight in blue when you hover a card over them

### ➕ Add New Application
- Click the **"+ Add"** button in any column
- Fill in company name, role, and other details
- Status defaults to "Applied" (change if needed)
- Submit to create

### ✏️ Edit Application
- Click any card to open the edit modal
- Update any field
- Delete the application with the red button if needed

### 🔄 Moving Applications
**Two ways to move:**
1. **Drag & Drop** (recommended):
   - Click and hold a card
   - Drag it to another column
   - Release to drop
   - Changes save automatically

2. **Edit Modal**:
   - Click a card
   - Change the "Status" dropdown
   - Submit to move

## Database

View all your data in the Prisma Studio GUI:

```bash
npx prisma studio
# Opens at http://localhost:5555
```

## What's Included

- ✅ Full Kanban board with 7 columns
- ✅ Drag-and-drop between columns
- ✅ Create, read, update, delete applications
- ✅ Form validation
- ✅ Local SQLite database
- ✅ Responsive design with Tailwind CSS
- ✅ TypeScript for type safety

## Next: Write Tests (Optional)

```bash
npm run test:watch  # Run tests in watch mode
```

Test files go in `components/__tests__/` and `lib/__tests__/`
