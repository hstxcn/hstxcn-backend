apps = [
]

urls = [
    (r"/collection/(?P<uuid>[0-9a-fA-F]{32})", "collection.CollectionHandler"),
    (r"/photographer/(?P<uuid>[0-9a-fA-F]{32})/collection", "collection.CollectionsHandler"),
    (r"/collection/(?P<uuid>[0-9a-fA-F]{32})/like", "collection.CollectionLikeHandler"),
    (r"/photographer/(?P<uuid>[0-9a-fA-F]{32})/collection/count", "collection.CollectionsCountHandler"),
    (r"/user/collection/(?P<uuid>[0-9a-fA-F]{32})", "collection.UserCollectionHandler"),
    (r"/user/collection", "collection.UserCollectionsHandler"),
    (r"/user/collection/(?P<col_id>[0-9a-fA-F]{32})/works/(?P<work_id>[0-9a-fA-F]{32})",
     "collection.UserCollectionWorkHandler"),
    (r"/user/collection/(?P<col_id>[0-9a-fA-F]{32})/works", "collection.UserCollectionWorksHandler"),
    (r"/home/banner/(?P<uuid>[0-9a-fA-F]{32})", "home.BannerHandler"),
    (r"/home/banner", "home.BannersHandler"),
    (r"/home/photographer/(?P<uuid>[0-9a-fA-F]{32})", "home.HomePhotographerHandler"),
    (r"/home/photographer", "home.HomePhotographersHandler"),
    (r"/home/collection/(?P<uuid>[0-9a-fA-F]{32})", "home.HomeCollectionHandler"),
    (r"/home/collection", "home.HomeCollectionsHandler"),
    (r"/image", "image.ImageUploadHandler"),
    (r"/photographer/(?P<uuid>[0-9a-fA-F]{32})", "photographer.PhotographerHandler"),
    (r"/photographer", "photographer.PhotographersHandler"),
    (r"/photographer/count", "photographer.PhotographersCountHandler"),
    (r"/photographer/search", "photographer.PhotographersSearchHandler"),
    (r"/photographer/option", "photographer.PhotographerOptionHandler"),
    (r"/theme/(?P<uuid>[0-9a-fA-F]{32})", "theme.ThemeHandler"),
    (r"/theme", "theme.ThemesHandler"),
    (r"/theme/count", "theme.ThemesCountHandler"),
    (r"/theme/(?P<theme_id>[0-9a-fA-F]{32})/collection/(?P<col_id>[0-9a-fA-F]{32})", "theme.ThemeCollectionHandler"),
    (r"/theme/(?P<uuid>[0-9a-fA-F]{32})/collection", "theme.ThemeCollectionsHandler"),
    (r"/theme/(?P<uuid>[0-9a-fA-F]{32})/collection/count", "theme.ThemeCollectionsCountHandler"),
    (r"/register", "user.RegisterHandler"),
    (r"/login", "user.LoginHandler"),
    (r"/profile", "user.ProfileHandler"),
    (r"/user", "user.ProfileHandler"),
    (r"/user/activate", "user.ActivateHandler"),
    (r"/user/(?P<uuid>[0-9a-fA-F]{32})/confirmation/(?P<token>.*)", "user.ConfirmationHandler"),
    (r"/user/(?P<uuid>[0-9a-fA-F]{32})/confirmation", "user.ResendConfirmationHandler"),
    (r"/users", "user.UserQueryHandler"),
]

