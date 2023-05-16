from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os
import json


def query_get_all_prs():
    # =================================================================
    # get a list of all prs for a given repository
    # =================================================================
    # "query_str": query_string
    # "has_next_page_path": This is the check for the next page of data formatted specifically for this query
    # "start_with_path": This is the path for the next page of data formatted specifically for this query
    #  "query_vars": These are the variables that are required internally for the query to run
    #       "loginOrg": "IQSS",
    #       "repo": "dataverse",
    #       "firstFew": 100,
    #       "startWith" - this is not used initially it's an interim variable that is used to store the cursor
    #
    # ---------------------------------------------------------------
    query_string = \
    """
    query ($loginOrg: String!, $repo: String!, $firstFew: Int, $startWith: String) {
        repository(followRenames:false, owner: $loginOrg, name: $repo) {
                id
                name
                url
                owner {
                    login
                }
                pullRequests (first: $firstFew, after: $startWith) {
                    totalCount
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        endCursor
                        startCursor
                    }
                    nodes {
                        ...prFields
                    }
                }
        }
    }
        """
    query_string = query_string + fragment_pr_fields_on_pullrequest()
    qry = {
        "query_str": query_string,
        "has_next_page_path": ["repository", "pullRequests", "pageInfo", "hasNextPage"],
        "start_with_path": ["repository", "pullRequests", "pageInfo", "endCursor"],
        "query_vars": {
            "loginOrg": "IQSS",
            "repo": "dataverse",
            "firstFew": 100,
            "startWith": ""
            }
        }
    return qry

def fragment_pr_fields_on_pullrequest():
    # =================================================================
    # this is a query fragment used within other queries
    # =================================================================

    fragment_string = \
    """
    fragment prFields on PullRequest {
       repository {
            name
        }
        title
        number
        id
        url
        closed
        closedAt
        labels (first: 10) {
          totalCount
            nodes {
                name
            }
        }
        closingIssuesReferences (first: 20){
            totalCount
            nodes {
                number
                }

        }
    }
    """
    return fragment_string