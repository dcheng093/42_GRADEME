#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

typedef struct node {
	enum {
		ADD,
		MULTI,
		VAL
	}	type;
	int	val;
	struct node	*l;
	struct node	*r;
}	node;

node	*new_node(node n)
{
	node	*ret = calloc(1, sizeof(n));

	if (!ret)
		return (NULL);
	*ret = n;
	return (ret);
}

void	destroy_tree(node *n)
{
	if (!n)
		return ;
	if (n->type != VAL)
	{
		destroy_tree(n->l);
		destroy_tree(n->r);
	}
	free(n);
}

void	unexpected(char c)
{
	if (c)
		printf("Unexpected token '%c'\n", c);
	else
		printf("Unexpected end of input\n");
}

int	accept(char **s, char c)
{
	if (**s == c)
	{
		(*s)++;
		return (1);
	}
	return (0);
}

int	expect(char **s, char c)
{
	if (accept(s, c))
		return (1);
	unexpected(**s);
	return (0);
}

static node	*parse_sum(char **s);

// a digit, or a sum in parentheses
static node	*parse_factor(char **s)
{
	node	*inside;

	if (isdigit((unsigned char)**s))
	{
		node	*leaf = new_node((node){.type = VAL, .val = **s - '0'});
		(*s)++;
		return (leaf);
	}
	if (accept(s, '('))
	{
		inside = parse_sum(s);
		if (!inside)
			return (NULL);
		if (!expect(s, ')'))
			return (destroy_tree(inside), NULL);
		return (inside);
	}
	unexpected(**s);
	return (NULL);
}

static node	*parse_product(char **s)
{
	node	*left;
	node	*right;
	node	*joined;

	left = parse_factor(s);
	while (left && accept(s, '*'))
	{
		right = parse_factor(s);
		if (!right)
			return (destroy_tree(left), NULL);
		joined = new_node((node){.type = MULTI, .l = left, .r = right});
		if (!joined)
			return (destroy_tree(left), destroy_tree(right), NULL);
		left = joined;
	}
	return (left);
}

static node	*parse_sum(char **s)
{
	node	*left;
	node	*right;
	node	*joined;

	left = parse_product(s);
	while (left && accept(s, '+'))
	{
		right = parse_product(s);
		if (!right)
			return (destroy_tree(left), NULL);
		joined = new_node((node){.type = ADD, .l = left, .r = right});
		if (!joined)
			return (destroy_tree(left), destroy_tree(right), NULL);
		left = joined;
	}
	return (left);
}

node	*parse_expr(char *s)
{
	node	*ret = parse_sum(&s);

	if (!ret)
		return (NULL);
	if (*s)
	{
		unexpected(*s);
		destroy_tree(ret);
		return (NULL);
	}
	return (ret);
}

int	eval_tree(node *tree)
{
	switch (tree->type)
	{
		case ADD:
			return (eval_tree(tree->l) + eval_tree(tree->r));
		case MULTI:
			return (eval_tree(tree->l) * eval_tree(tree->r));
		case VAL:
			return (tree->val);
	}
	return (0);
}

int	main(int argc, char **argv)
{
	if (argc != 2)
		return (1);
	node	*tree = parse_expr(argv[1]);
	if (!tree)
		return (1);
	printf("%d\n", eval_tree(tree));
	destroy_tree(tree);
}
