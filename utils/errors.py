# -*- coding: utf-8 -*-
"""Contains common errors for the application"""


class SignoxeBaseError(Exception):
    """Base error class for our application"""
    pass


class AssetError(SignoxeBaseError):
    """Base class for all asset-related errors"""
    pass


class InvalidAssetError(AssetError):
    """
    Error for cases when an asset is invalid. For instance a calendar asset that has no calendar
    data.
    """
    pass


class NoContentAssetError(AssetError):
    """
    Error for cases when an asset has no content currently. For instance a feed asset that has
    no snippet for today, or a calendar asset with with data for the current time.
    """
    pass
