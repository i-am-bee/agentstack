import { useMCPClient } from '@/contexts/MCPClient';
import { useQuery } from '@tanstack/react-query';
import { agentKeys } from '../keys';
import { Agent, ListAgentsParams } from '../types';

interface Props {
  params?: ListAgentsParams;
}

export function useListAgents({ params }: Props = {}) {
  const client = useMCPClient();

  const query = useQuery({
    queryKey: agentKeys.list(params),
    queryFn: () => client.listAgents(params),
    select: (data) => data?.agents as Agent[],
  });

  return query;
}
