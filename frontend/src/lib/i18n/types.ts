export type Locale = {
  metadata: {
    title: string;
    description: string;
    lang: string;
  };
  auth: {
    login: {
      brand: string;
      subtitle: string;
      heading: string;
      description: string;
      emailLabel: string;
      passwordLabel: string;
      companyIdLabel: string;
      companyIdPlaceholder: string;
      signIn: string;
      signingIn: string;
      enterpriseAuth: string;
      heroHeading: string;
      heroDescription: string;
      featureTenant: string;
      featureRoles: string;
      featureTokens: string;
      errorFallback: string;
    };
    logout: {
      button: string;
    };
    protected: {
      loading: string;
    };
  };
  nav: {
    sidebar: {
      brand: string;
      subtitle: string;
      workspace: string;
      platform: string;
      customers: string;
      products: string;
      chats: string;
      analytics: string;
      automations: string;
      aiSales: string;
      settings: string;
      closeNav: string;
      foundationLabel: string;
      foundationDesc: string;
    };
    topbar: {
      openNav: string;
      toggleNav: string;
      searchPlaceholder: string;
      demoCompany: string;
      notifications: string;
      avatarInitials: string;
    };
  };
  dashboard: {
    home: {
      eyebrow: string;
      title: string;
      description: string;
      metricActiveCustomers: string;
      metricCatalogProducts: string;
      metricOpenChats: string;
      metricAutomationRules: string;
      metricCustomersReady: string;
      metricProductsReady: string;
      metricChatsReady: string;
      metricAutomationsReady: string;
      metricCustomersFooter: string;
      metricProductsFooter: string;
      metricChatsFooter: string;
      metricAutomationsFooter: string;
      moduleReadiness: string;
      moduleReadinessDesc: string;
      viewRoadmap: string;
      tableHeaderModule: string;
      tableHeaderWorkspace: string;
      tableHeaderStatus: string;
      tableHeaderNext: string;
      rowCustomersModule: string;
      rowCustomersWorkspace: string;
      rowCustomersNext: string;
      rowProductsModule: string;
      rowProductsWorkspace: string;
      rowProductsNext: string;
      rowChatsModule: string;
      rowChatsWorkspace: string;
      rowChatsNext: string;
      rowAnalyticsModule: string;
      rowAnalyticsWorkspace: string;
      rowAnalyticsNext: string;
      rowAutomationsModule: string;
      rowAutomationsWorkspace: string;
      rowAutomationsNext: string;
      noModulesTitle: string;
      noModulesDesc: string;
      loadingSection: string;
      loadingDesc: string;
      nextPhase: string;
      nextPhaseDesc: string;
      emptyTitle: string;
      emptyDesc: string;
      preparedness: string;
      prepared: string;
      shell: string;
      deferred: string;
    };
  };
  customers: {
    page: {
      eyebrow: string;
      title: string;
      description: string;
      importButton: string;
    };
    workspace: {
      errorLoad: string;
      searchPlaceholder: string;
      allStatuses: string;
      filters: string;
      createButton: string;
      tableHeaderCustomer: string;
      tableHeaderLeadStatus: string;
      tableHeaderChannel: string;
      tableHeaderTags: string;
      tableHeaderSource: string;
      emptyTitle: string;
      emptyDesc: string;
      paginationShowing: string;
      paginationNone: string;
      previous: string;
      next: string;
      fallbackName: string;
      fallbackNotSet: string;
      fallbackSource: string;
    };
    form: {
      createTitle: string;
      editTitle: string;
      description: string;
      fullName: string;
      email: string;
      leadStatus: string;
      phone: string;
      whatsapp: string;
      instagram: string;
      source: string;
      tags: string;
      tagsPlaceholder: string;
      notes: string;
      cancel: string;
      saving: string;
      save: string;
      errorFallback: string;
    };
    profile: {
      emptyTitle: string;
      emptyDesc: string;
      email: string;
      phone: string;
      whatsapp: string;
      instagram: string;
      noSource: string;
      notProvided: string;
      tags: string;
      noTags: string;
      notes: string;
      noNotes: string;
      edit: string;
      delete: string;
      deleting: string;
      errorDelete: string;
    };
    status: {
      new: string;
      interested: string;
      negotiating: string;
      won: string;
      lost: string;
    };
  };
  conversations: {
    page: {
      eyebrow: string;
      title: string;
      description: string;
    };
    workspace: {
      errorLoad: string;
      searchPlaceholder: string;
      allStatuses: string;
      filters: string;
      title: string;
      tableHeaderConversation: string;
      tableHeaderStatus: string;
      tableHeaderUpdated: string;
      emptyTitle: string;
      emptyDesc: string;
      paginationShowing: string;
      paginationNone: string;
      previous: string;
      next: string;
      noSubject: string;
      conversationLabel: string;
      conversationsLabel: string;
      selectChat: string;
      selectChatDesc: string;
      noMessages: string;
      noMessagesDesc: string;
      messagePlaceholder: string;
      sendError: string;
      closedChat: string;
    };
    status: {
      open: string;
      pending: string;
      closed: string;
    };
  };
  products: {
    page: {
      eyebrow: string;
      title: string;
      description: string;
    };
    workspace: {
      errorLoad: string;
      searchPlaceholder: string;
      allStatuses: string;
      filters: string;
      createButton: string;
      tableHeaderProduct: string;
      tableHeaderStatus: string;
      tableHeaderCategory: string;
      tableHeaderVariants: string;
      tableHeaderPrice: string;
      emptyTitle: string;
      emptyDesc: string;
      paginationShowing: string;
      paginationNone: string;
      previous: string;
      next: string;
      fallbackCategory: string;
    };
    form: {
      createTitle: string;
      editTitle: string;
      description: string;
      productName: string;
      category: string;
      categoryPlaceholder: string;
      status: string;
      basePrice: string;
      pricePlaceholder: string;
      descriptionLabel: string;
      descriptionPlaceholder: string;
      cancel: string;
      saving: string;
      save: string;
      errorFallback: string;
    };
    detail: {
      emptyTitle: string;
      emptyDesc: string;
      category: string;
      basePrice: string;
      description: string;
      variantsSection: string;
      imagesSection: string;
      noAttributes: string;
      stock: string;
      reserved: string;
      deleteVariant: string;
      noVariants: string;
      noImage: string;
      deleteImage: string;
      noImages: string;
      imageUrlPlaceholder: string;
      adding: string;
      add: string;
      edit: string;
      delete: string;
      deleting: string;
      errorDelete: string;
      errorAddImage: string;
    };
    variantForm: {
      heading: string;
      skuRequired: string;
      skuPlaceholder: string;
      sizePlaceholder: string;
      colorPlaceholder: string;
      stockPlaceholder: string;
      pricePlaceholder: string;
      adding: string;
      add: string;
      errorAdd: string;
    };
    status: {
      active: string;
      inactive: string;
      draft: string;
    };
  };
  sales: {
    page: {
      eyebrow: string;
      title: string;
      description: string;
    };
    hero: {
      hotLeads: string;
      interested: string;
      negotiation: string;
      converted: string;
      hotLeadsDesc: string;
      interestedDesc: string;
      negotiationDesc: string;
      convertedDesc: string;
    };
    topLeads: {
      title: string;
      description: string;
      name: string;
      score: string;
      status: string;
      priority: string;
      activity: string;
      lastInteraction: string;
      probability: string;
      emptyTitle: string;
      emptyDesc: string;
    };
    recommendations: {
      title: string;
      description: string;
      followUp: string;
      hotLeads: string;
      negotiation: string;
      inactive: string;
      upsell: string;
      viewProfile: string;
      noFollowUp: string;
      noHotLeads: string;
      noNegotiation: string;
      noInactive: string;
    };
    intents: {
      title: string;
      description: string;
      purchase: string;
      pricing: string;
      negotiation: string;
      shipping: string;
      unknown: string;
      noData: string;
    };
    activity: {
      title: string;
      description: string;
      message: string;
      conversation: string;
      statusChange: string;
      noActivity: string;
      noActivityDesc: string;
    };
    profile: {
      title: string;
      description: string;
      summary: string;
      intents: string;
      messages: string;
      conversations: string;
      salesSummary: string;
      close: string;
    };
    errors: {
      loadInsights: string;
      loadLeads: string;
      loadRecommendations: string;
      loadActivity: string;
      loadProfile: string;
    };
    loading: {
      insights: string;
      leads: string;
      recommendations: string;
      activity: string;
    };
  };
  common: {
    modal: {
      close: string;
    };
    table: {
      noModules: string;
      noModulesDesc: string;
    };
    statusBadge: {
      prepared: string;
      ready: string;
    };
    metricCard: {
      ready: string;
      shell: string;
      deferred: string;
    };
    errors: {
      unknown: string;
      apiFailed: string;
    };
  };
};
