/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// import { ErrorBoundary } from 'react-error-boundary';
// import { BrowserRouter, Route, Routes } from 'react-router';

// import { ErrorFallback } from '#components/fallbacks/ErrorFallback.tsx';
// import { AppLayout } from '#components/layouts/AppLayout.tsx';
// import { AppProvider } from '#contexts/App/AppProvider.tsx';
// import { AppConfigProvider } from '#contexts/AppConfig/AppConfigProvider.tsx';
// import { ModalProvider } from '#contexts/Modal/ModalProvider.tsx';
// import { QueryProvider } from '#contexts/QueryProvider/QueryProvider.tsx';
// import { ThemeProvider } from '#contexts/Theme/ThemeProvider.tsx';
// import { ToastProvider } from '#contexts/Toast/ToastProvider.tsx';
// import { ComposeLanding } from '#modules/compose/ComposeLanding.tsx';
// import { ComposeSequential } from '#modules/compose/ComposeSequential.tsx';
// import { Agents } from '#pages/Agents.tsx';
// import { Agent } from '#pages/agents/Agent.tsx';
// import { Landing } from '#pages/Landing.tsx';
// import { NotFound } from '#pages/NotFound.tsx';
// import { AgentRunPage } from '#pages/runs/AgentRunPage.tsx';
// import { Settings } from '#pages/Settings.tsx';
// import { routeDefinitions } from '#utils/router.ts';

// export function App() {
//   return (
//     <ErrorBoundary FallbackComponent={ErrorFallback}>
//       <ToastProvider>
//         <QueryProvider>
//           <ThemeProvider>
//             <ModalProvider>
//               <AppConfigProvider>
//                 <AppProvider>
//                   <BrowserRouter>
//                     <Routes>
//                       <Route element={<AppLayout />}>
//                         <Route path={routeDefinitions.home()} element={<Landing />} />
//                         <Route path={routeDefinitions.agents()} element={<Agents />} />
//                         <Route path={routeDefinitions.agentDetail()} element={<Agent />} />
//                         <Route path={routeDefinitions.agentRun()} element={<AgentRunPage />} />
//                         <Route path={routeDefinitions.playground()} element={<ComposeLanding />} />
//                         <Route path={routeDefinitions.playgroundSequential()} element={<ComposeSequential />} />
//                         <Route path={routeDefinitions.settings()} element={<Settings />} />
//                         <Route path="*" element={<NotFound />} />
//                       </Route>
//                     </Routes>
//                   </BrowserRouter>
//                 </AppProvider>
//               </AppConfigProvider>
//             </ModalProvider>
//           </ThemeProvider>
//         </QueryProvider>
//       </ToastProvider>
//     </ErrorBoundary>
//   );
// }
