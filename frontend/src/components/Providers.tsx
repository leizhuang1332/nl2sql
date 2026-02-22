'use client';

import React from 'react';
import { ConfigProvider, theme } from 'antd';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#22C55E',
          colorBgBase: '#0F172A',
          colorBgContainer: '#1E293B',
          colorBgElevated: '#334155',
          colorBorder: '#334155',
          colorBorderSecondary: '#1E293B',
          colorText: '#F8FAFC',
          colorTextSecondary: '#94A3B8',
          fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          borderRadius: 8,
        },
        components: {
          Layout: {
            headerBg: '#1E293B',
            siderBg: '#0F172A',
            bodyBg: '#0F172A',
          },
          Menu: {
            darkItemBg: '#0F172A',
            darkItemSelectedBg: '#1E293B',
          },
          Table: {
            headerBg: '#1E293B',
            rowHoverBg: '#1E293B',
          },
          Card: {
            colorBgContainer: '#1E293B',
          },
          Input: {
            colorBgContainer: '#1E293B',
          },
          Tree: {
            directoryNodeSelectedBg: '#22C55E20',
            directoryNodeSelectedColor: '#22C55E',
          },
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
