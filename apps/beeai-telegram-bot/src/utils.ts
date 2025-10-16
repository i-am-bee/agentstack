export async function createContext() {
  const response = await fetch('http://localhost:8333/api/v1/contexts', { 
    method: 'POST',
        headers: {
        "content-type": "application/json"
    },
    body: JSON.stringify({})
  });
  if (!response.ok) throw new Error(response.statusText)
  return await response.json()
}

export async function createContextToken(
  context_id: string) {
  const response = await fetch(`http://localhost:8333/api/v1/contexts/${context_id}/token`, { 
    method: "POST",
    headers: {
        "content-type": "application/json"
    },
    body: JSON.stringify({ grant_global_permissions: {
        llm: ['*'],
        a2a_proxy: [],
        contexts: [],
        embeddings: ['*'],
        feedback: [],
        files: [],
        providers: [],
        provider_variables: [],
        model_providers: [],
        mcp_providers: [],
        mcp_proxy: [],
        mcp_tools: [],
        vector_stores: [],
        context_data: [],
      }, grant_context_permissions: {
        files: ['*'],
        vector_stores: ['*'],
        context_data: ['*'],
      } }),
  });
  if (!response.ok) throw new Error(response.statusText)
  return await response.json()
}