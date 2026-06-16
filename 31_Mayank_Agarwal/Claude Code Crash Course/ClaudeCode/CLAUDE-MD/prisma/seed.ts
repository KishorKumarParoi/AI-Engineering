import prisma from '@/lib/prisma';

const testApplications = [
  {
    companyName: 'Google',
    roleTitle: 'Senior Frontend Engineer',
    status: 'interviewing',
    jobUrl: 'https://careers.google.com/jobs/results/123',
    location: 'Mountain View, CA',
    salaryRange: '$180k - $220k',
    appliedDate: '2026-04-15',
    notes: 'Great opportunity for growth. First round interview scheduled.',
    contactName: 'Sarah Chen',
    contactEmail: 'sarah@google.com',
    priority: 1,
  },
  {
    companyName: 'Meta',
    roleTitle: 'Full Stack Engineer',
    status: 'phone_screen',
    jobUrl: 'https://www.metacareers.com/jobs/456',
    location: 'Menlo Park, CA',
    salaryRange: '$170k - $210k',
    appliedDate: '2026-04-18',
    notes: 'Phone screen with recruiter next week.',
    contactName: 'Alex Rodriguez',
    contactEmail: 'alex.rodriguez@meta.com',
    priority: 2,
  },
  {
    companyName: 'Microsoft',
    roleTitle: 'Software Engineer II',
    status: 'applied',
    jobUrl: 'https://careers.microsoft.com/us/jobs/789',
    location: 'Seattle, WA',
    salaryRange: '$160k - $200k',
    appliedDate: '2026-04-25',
    notes: 'Application submitted. Waiting to hear back.',
    contactName: null,
    contactEmail: null,
    priority: 3,
  },
  {
    companyName: 'Stripe',
    roleTitle: 'Product Engineer',
    status: 'offer',
    jobUrl: 'https://stripe.com/jobs/listing/1011',
    location: 'San Francisco, CA',
    salaryRange: '$190k - $230k',
    appliedDate: '2026-03-20',
    notes: 'Offer received! Negotiating salary and benefits.',
    contactName: 'Jamie Park',
    contactEmail: 'jamie@stripe.com',
    priority: 0,
  },
  {
    companyName: 'Amazon',
    roleTitle: 'Backend Engineer',
    status: 'rejected',
    jobUrl: 'https://www.amazon.jobs/en/jobs/1213',
    location: 'Austin, TX',
    salaryRange: '$150k - $190k',
    appliedDate: '2026-04-01',
    notes: 'Rejected after coding interview. Good learning experience.',
    contactName: 'Marcus Johnson',
    contactEmail: 'marcus.j@amazon.com',
    priority: 4,
  },
];

async function main() {
  try {
    console.log('🌱 Seeding test job applications...');

    for (const app of testApplications) {
      const created = await prisma.jobApplication.create({
        data: app,
      });
      console.log(`✓ Created: ${created.companyName} - ${created.roleTitle}`);
    }

    console.log('✅ Successfully seeded 5 test applications!');
  } catch (error) {
    console.error('❌ Seeding failed:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

main();
