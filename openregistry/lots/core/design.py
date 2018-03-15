# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition
from openprocurement.api import design


FIELDS = [
    'status',
    'lotID',
    'lotType'
]

CHANGES_FIELDS = FIELDS + [
    'dateModified',
]


def add_design():
    for i, j in globals().items():
        if "_view" in i:
            setattr(design, i, j)


lots_all_view = ViewDefinition('lot', 'all', '''function(doc) {
    if(doc.doc_type == 'Lot') {
        emit(doc.lotID, null);
    }
}''')


lots_by_dateModified_view = ViewDefinition('lots', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Lot' && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

lots_real_by_dateModified_view = ViewDefinition('lots', 'real_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Lot' && doc.status != 'draft' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

lots_test_by_dateModified_view = ViewDefinition('lots', 'test_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Lot' && doc.status != 'draft' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

lots_by_local_seq_view = ViewDefinition('lots', 'by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Lot' && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

lots_real_by_local_seq_view = ViewDefinition('lots', 'real_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Lot' && doc.status != 'draft' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

lots_test_by_local_seq_view = ViewDefinition('lots', 'test_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Lot' && doc.status != 'draft' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)


VIEW_MAP = {
    u'': lots_real_by_dateModified_view,
    u'test': lots_test_by_dateModified_view,
    u'_all_': lots_by_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u'': lots_real_by_local_seq_view,
    u'test': lots_test_by_local_seq_view,
    u'_all_': lots_by_local_seq_view,
}
FEED = {
    u'dateModified': VIEW_MAP,
    u'changes': CHANGES_VIEW_MAP,
}
