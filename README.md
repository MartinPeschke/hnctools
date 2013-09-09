hnctools
========



Pyramid, mako, formencode, babel based tools for:

*hnc.apiclient*
- was JSONMapperHGMMPFork
- is Json Client for Backend API   


*hnc.forms*
- a localized form library for twitter bootstrap (2 and 3)
- all widget can be inherited and custom templates can be provided per widget   
- best used tobgether with [hncajax](https://github.com/MartinPeschke/hncajax) for ajax submission, error highlighting and advanced controls like typeaheads, repeating forms, tags    
 
 
*hnc.tools*
- extends pyramid.request
- provides pluggable i18n support
- some routing constructs, for URLDispatch and traversal
- standard oauth library, based on Culver's at al work from years and years ago, still seems to work, somewhat

*hnc.apps*
- contains only static content managing for now, this is a replacement for poedit, but uses the gettext babel/lingua message extraction/catalog machinery
