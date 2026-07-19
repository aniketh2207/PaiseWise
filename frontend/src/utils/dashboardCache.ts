export const dashboardCache = {
  cache: {} as Record<string, any>,
  needsRefresh: true,
  invalidate() {
    this.needsRefresh = true;
  }
};
