import React from "react";
import { Body, Container, Head, Text, Html, Preview, Section, Hr } from "@react-email/components";
import { Tailwind } from "@react-email/tailwind";

interface Stock {
  code: string;
  currentPrice: number;
  thresholds: {
    lower: number[];
    upper: number[];
  }
}

interface EmailTemplateProps {
  name: string;
  stocks: Stock[];
}

export const EmailTemplate =({ name, stocks }: EmailTemplateProps) => {
  const date = new Date().toLocaleDateString();

  return (
    <Html>
      <Head />
      <Preview>The share price update for {date}</Preview>

      <Tailwind>
        <Body className="bg-white my-auto mx-auto font-sans px-2">
          <Container className="border border-solid border-[#eaeaea] rounded my-[40px] mx-auto p-[20px] max-w-[465px]">
            <Text className="text-black text-[14px] leading-[24px]">
              Hello {name},
            </Text>
            <Section className='space-y-4'>
              {
                stocks.map(stock => {
                  const padding = (Math.max(...stock.thresholds.upper) - Math.min(...stock.thresholds.lower)) * 0.1;
                  const lowerBound = Math.min(...stock.thresholds.lower) - padding;
                  const upperBound = Math.max(...stock.thresholds.upper) + padding;

                  const totalDistance = upperBound - lowerBound;
                  const lowerToCurrentDistance = Math.abs(lowerBound - stock.currentPrice);
                  const lowerToCurrentPercentage = (lowerToCurrentDistance / totalDistance) * 100;
                  const upperToCurrentDistance = Math.abs(upperBound - stock.currentPrice);
                  const upperToCurrentPercentage = (upperToCurrentDistance / totalDistance) * 100;

                  const greyZoneDistance = Math.min(...stock.thresholds.upper) - Math.max(...stock.thresholds.lower);
                  const greyZonePercentage = (greyZoneDistance / totalDistance) * 100;
                  const greyZoneOffset = ((Math.max(...stock.thresholds.lower) - lowerBound) / totalDistance) * 100;

                  return (
                    <div className="border rounded p-4">
                      <div className="flex justify-between mb-2 font-bold">
                        <span>{stock.code}</span>
                        <span className="px-2 py-1 rounded bg-blue-200">${stock.currentPrice}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Thresholds:</span>
                        <span>
                          Lower: {stock.thresholds.lower.join(', ')}<br/>
                          Upper: {stock.thresholds.upper.join(', ')}
                        </span>
                      </div>
                      <div className="mt-4">
                        <div className="relative h-4 border rounded w-full">
                          <div className="absolute h-4 w-full bg-gray-200"></div>
                          <div className="absolute h-4 bg-green-300" style={{
                            width: `${lowerToCurrentPercentage}%` 
                          }}></div>
                          <div className="absolute h-4 bg-red-300" style={{ 
                            left:`${lowerToCurrentPercentage}%`,  
                            width: `${upperToCurrentPercentage}%` 
                          }}></div>
                          <div className="absolute h-4 bg-gray-300" style={{
                            left: `${greyZoneOffset}%`,
                            width: `${greyZonePercentage}%`
                          }}></div>
                          <div className="absolute h-4 bg-red-500" style={{
                            left: `${lowerToCurrentPercentage}%`,
                            width: `0.5%`
                          }}></div>
                          {[...stock.thresholds.lower, ...stock.thresholds.upper].map(thresh => {
                            const percentage = ((thresh - lowerBound) / totalDistance) * 100;
                            return (
                              <div className="absolute h-4 bg-black" style={{
                                left: `${percentage}%`,
                                width: `0.2%`
                              }}></div>
                            )
                          })}
                        </div>
                        <div className='flex flex-row w-full justify-between text-xs text-gray-500'>
                          <span>${lowerBound}</span>
                          <span>${upperBound}</span>
                        </div>
                      </div>
                      <Hr />
                    </div>
                  )
                })
              }
            </Section>
          </Container>
        </Body>
      </Tailwind>
    </Html>
  )
}

export default EmailTemplate;