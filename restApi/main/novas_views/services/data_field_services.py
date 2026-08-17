from rest_framework.exceptions import ValidationError


class DataFieldService:

    def filter_queryset(
        self, queryset, field, value, allowed_fields, special_filters=None
    ):
        if field and value:
            if field not in allowed_fields:
                raise ValidationError(
                    {"error": f"O campo '{field}' não é permitido para busca."}
                )
            if special_filters and field in special_filters:
                queryset = queryset.filter(**{special_filters[field]: value})
            else:
                queryset = queryset.filter(**{f"{field}__icontains": value})
        return queryset

    def order_queryset(
        self,
        queryset,
        order_by,
        valid_order_fields,
        annotate_fields=None,
        default_order="id",
    ):
        if not order_by:
            return queryset.order_by(default_order)
        allowed_fields = list(valid_order_fields)
        if annotate_fields:
            allowed_fields.extend(annotate_fields)
        allowed_order = set(allowed_fields + [f"-{field}" for field in allowed_fields])
        if order_by in allowed_order:
            return queryset.order_by(order_by)
        base_field = order_by[1:] if order_by.startswith("-") else order_by
        if base_field in valid_order_fields:
            return queryset.order_by(order_by)
        return queryset.order_by(default_order)

    def filter_and_order_queryset(
        self,
        queryset,
        field,
        value,
        order_by,
        allowed_fields,
        valid_order_fields,
        annotate_fields=None,
        special_filters=None,
        default_order="id",
    ):
        queryset = self.filter_queryset(
            queryset, field, value, allowed_fields, special_filters=special_filters
        )
        return self.order_queryset(
            queryset,
            order_by,
            valid_order_fields,
            annotate_fields=annotate_fields,
            default_order=default_order,
        )
