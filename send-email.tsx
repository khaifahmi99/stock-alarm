import React from 'react';
import assert from 'assert';
import { Resend } from 'resend';
import dotenv from 'dotenv';
import { EmailTemplate } from './EmailTemplate';
import stocks from './metadata.json';

dotenv.config();

async function main() {
  assert(process.env.RESEND_API_KEY, 'Resend API key is required');
  assert(process.env.PRIMARY_RECEPIENT, 'Primary recipient email is required');
  
  const resend = new Resend(process.env.RESEND_API_KEY);
  const RECEPIENT_EMAIL = process.env.PRIMARY_RECEPIENT ?? '';

  try {
    await resend.emails.send({
      from: "MarketNotification Graphics <app-market-notification@resend.dev>",
      to: RECEPIENT_EMAIL,
      subject: 'Your Stock Summary Today',
      react: <EmailTemplate name="" stocks={stocks} />,
    });

    console.log('Email sent!');
  } catch (error) {
    console.error('Error sending email:', error);
  }
}

main();
