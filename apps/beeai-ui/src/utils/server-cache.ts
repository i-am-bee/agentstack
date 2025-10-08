import { Cacheable } from 'cacheable';

export const cache = new Cacheable({
  ttl: 60 * 5, // 5 minutes
});

export const cacheKeys = {
  refreshToken: (refreshToken: string) => `refreshToken:${refreshToken}`,
};
