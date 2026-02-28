from django.urls import path
from file_share.apps.file.views import *

urlpatterns = [
    path(
        "upload/",
        UploadFileCreateView.as_view(),
        name="upload-file"
    ),
    path(
        "download/<uuid:fie_id>/",
        DownloadFileView.as_view(),
        name="download-file"
    ),
    path(
        "",
        FileListView.as_view(),
        name="files-list"
    ),
    path(
        "<uuid:file_id>/",
        RetrieveUpdateDestroyFileView.as_view(),
        name="retrieve-update-destroy"
    ),
    path(
        "shares/",
        SharedFilesListView.as_view(),
        name="shared-file-list"
    ),
    path(
        "shares/<uuid:file_id>/to/<uuid:user_id>/",
        ShareFileCreateView.as_view(),
        name="share-files"
    ),
    path(
        "unshare/<uuid:file_share_id>",
        UnshareFileDeleteView.as_view(),
        name="unshare"
    ),

]
