import json

import pytest

from saleor.dashboard.category.forms import CategoryForm
from saleor.product.models import Category, ProductAttribute


def get_content(response):
    return json.loads(response.content.decode('utf8'))


def assert_success(content):
    assert 'errors' not in content
    assert 'data' in content


def assert_corresponding_fields(iterable_data, queryset, fields):
    assert len(iterable_data) == queryset.count()
    for (data, obj) in zip(iterable_data, queryset):
        for field in fields:
            assert str(data[field]) == str(getattr(obj, field))


@pytest.mark.django_db()
def test_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = """
        query {
            category(pk: %(category_pk)s) {
                pk
                name
                productsCount
                children {
                    edges {
                        node {
                             name
                        }
                    }
                }
            }
        }
    """ % {'category_pk': category.pk}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    category_data = content['data']['category']
    assert category_data is not None
    assert int(category_data['pk']) == category.pk
    assert category_data['name'] == category.name
    assert category_data['productsCount'] == category.products.count()
    assert category_data['children']['edges'] == []


@pytest.mark.django_db()
def test_product_query(client, product_in_stock):
    category = Category.objects.first()
    product = category.products.first()
    query = """
        query {
            category(pk: %(category_pk)s) {
                products {
                    edges {
                        node {
                            pk
                            name
                            url
                            thumbnailUrl
                            images { url }
                            variants {
                                name
                                stockQuantity
                            }
                            availability {
                                available,
                                priceRange {
                                    minPrice {
                                        gross
                                        net
                                        currency
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """ % {'category_pk': category.pk}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    assert content['data']['category'] is not None
    product_edges_data = content['data']['category']['products']['edges']
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]['node']
    assert int(product_data['pk']) == product.pk
    assert product_data['name'] == product.name
    assert product_data['url'] == product.get_absolute_url()
    gross = product_data['availability']['priceRange']['minPrice']['gross']
    assert float(gross) == float(product.price.gross)


@pytest.mark.django_db()
def test_filter_product_by_attributes(client, product_in_stock):
    category = Category.objects.first()
    product_attr = product_in_stock.product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    filter_by = "%s:%s" % (product_attr.name, attr_value.slug)
    query = """
        query {
            category(pk: %(category_pk)s) {
                products(attributes: ["%(filter_by)s"]) {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        }
    """ % {'category_pk': category.pk, 'filter_by': filter_by}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    product_data = content['data']['category']['products']['edges'][0]['node']
    assert product_data['name'] == product_in_stock.name


@pytest.mark.django_db()
def test_attributes_query(client, product_in_stock):
    attributes = ProductAttribute.objects.prefetch_related('values')
    query = """
        query {
            attributes {
                pk
                name
                slug
                values {
                    pk
                    name
                    slug
                }
            }
        }
    """
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)
    attributes_data = content['data']['attributes']
    assert_corresponding_fields(attributes_data, attributes, ['pk', 'name'])


@pytest.mark.django_db()
def test_attributes_in_category_query(client, product_in_stock):
    category = Category.objects.first()
    query = """
        query {
            attributes(categoryPk: %(category_pk)s) {
                pk
                name
                slug
                values {
                    pk
                    name
                    slug
                }
            }
        }
    """ % {'category_pk': category.pk}
    response = client.post('/graphql/', {'query': query})
    content = get_content(response)
    assert_success(content)


def test_category_create_mutation(client):
    query = """
        mutation($name: String, $description: String, $parent: Int) {
            categoryCreate(data: {
                name: $name
                description: $description
                parent: $parent}
            ) {
                category {
                    pk
                    name
                    slug
                    description
                    parent {
                        pk
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """

    category_name = 'Test category'
    category_description = 'Test description'

    # test creating root category
    variables = json.dumps({
        'name': category_name, 'description': category_description})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description
    assert not data['category']['parent']

    # test creating subcategory
    parent_pk = data['category']['pk']
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'parent': int(parent_pk)})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryCreate']
    assert data['errors'] == []
    assert data['category']['parent']['pk'] == parent_pk


def test_category_update_mutation(client, default_category):
    query = """
        mutation($pk: Int, $name: String, $description: String, $parent: Int) {
            categoryUpdate(
                pk: $pk,
                data: {
                    name: $name
                    description: $description
                    parent: $parent}
            ) {
                category {
                    pk
                    name
                    slug
                    description
                    parent {
                        pk
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """

    category_name = 'Updated name'
    category_description = 'Updated description'

    # test creating root category
    variables = json.dumps({
        'name': category_name, 'description': category_description,
        'pk': default_category.pk})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryUpdate']
    assert data['errors'] == []
    assert data['category']['pk'] == str(default_category.pk)
    assert data['category']['name'] == category_name
    assert data['category']['description'] == category_description
    assert not data['category']['parent']


def test_category_delete_mutation(client, default_category):
    query = """
        mutation($pk: Int) {
            categoryDelete(pk: $pk) {
                category {
                    name
                    pk
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    variables = json.dumps({'pk': default_category.pk})
    response = client.post(
        '/graphql/', {'query': query, 'variables': variables})
    content = get_content(response)
    assert 'errors' not in content
    data = content['data']['categoryDelete']
    assert data['category']['pk'] is None
    assert data['category']['name'] == default_category.name
